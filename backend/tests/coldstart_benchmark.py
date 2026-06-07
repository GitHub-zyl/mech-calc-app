"""冷启动效应压测脚本 (Task 5 验证)

测试目标:
- 模拟 10 个用户同时向 /api/history 写入数据
- 对比优化前后的首次请求响应时间
- 验证冷启动比例是否从 8.9x 压降到 ≤3x
- 收集吞吐量、错误率、数据完整性等指标

使用方法:
    # 优化后 (默认):
    python -m backend.tests.coldstart_benchmark

    # 禁用预热 (基线对比):
    DISABLE_DB_WARMUP=1 python -m backend.app
    python -m backend.tests.coldstart_benchmark --label baseline

报告输出:
    coldstart_report_<label>_<timestamp>.json
"""
import argparse
import json
import os
import statistics
import sys
import threading
import time
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# UTF-8 输出
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import requests

BASE = "http://127.0.0.1:9091"
DEFAULT_USERS = 10
DEFAULT_PER_USER = 8  # 10 用户 x 8 请求 = 80 总请求


def _ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log(msg):
    try:
        print(f"[{_ts()}] {msg}", flush=True)
    except UnicodeEncodeError:
        safe = msg.encode('gbk', errors='replace').decode('gbk', errors='replace')
        print(f"[{_ts()}] {safe}", flush=True)


def _generate_payload(user_id: int, iter_id: int, user_tag: str) -> Dict[str, Any]:
    """生成真实业务场景的测试数据."""
    import random
    categories = ['bearing', 'gear', 'shaft', 'bolt', 'weld', 'spring', 'brake']
    return {
        'category': f'{user_tag}_{random.choice(categories)}',
        'endpoint': f'/api/coldstart/test/{user_id}/{iter_id}',
        'calc_id': f'coldstart-{user_tag}-{user_id}-{iter_id}',
        'input': {
            'user_id': user_id,
            'iteration': iter_id,
            'thread_id': threading.get_ident(),
            'timestamp': time.time(),
            'params': {
                'C': round(random.uniform(5.0, 50.0), 2),
                'P': round(random.uniform(1.0, 20.0), 2),
                'n': random.randint(500, 5000),
            }
        },
        'output': {
            'result': round(random.uniform(10.0, 1000.0), 3),
            'thread_name': f'User-{user_id:02d}',
            'computation_time_ms': round(random.uniform(0.1, 5.0), 3),
        },
        'duration_ms': round(random.uniform(0.5, 5.0), 3),
        'client_ip': f'127.0.0.{user_id + 1}',
    }


def worker(user_id: int, per_user: int, results: List[Dict[str, Any]],
           results_lock: threading.Lock, start_barrier: threading.Barrier,
           user_tag: str) -> None:
    """单个用户的工作线程. 写入 per_user 条记录."""
    thread_name = f"user_{user_id}"
    for i in range(per_user):
        # 第一轮: 等待所有线程就绪, 最大化冷启动瞬间并发
        if i == 0:
            start_barrier.wait()
        payload = _generate_payload(user_id, i, user_tag)
        ts_start = time.time()
        rec_id = None
        status_code = None
        error_type = None
        error_msg = None
        try:
            r = requests.post(f"{BASE}/api/history", json=payload, timeout=10)
            status_code = r.status_code
            if status_code == 200:
                rec_id = r.json().get('data', {}).get('id')
        except requests.exceptions.Timeout:
            error_type = 'timeout'
            error_msg = 'request timeout (>10s)'
        except requests.exceptions.ConnectionError as e:
            error_type = 'connection'
            error_msg = str(e)[:200]
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)[:200]

        ts_end = time.time()
        duration_ms = (ts_end - ts_start) * 1000

        rec = {
            'user_id': user_id,
            'iteration': i,
            'thread_name': thread_name,
            'thread_id': threading.get_ident(),
            'ts_start': ts_start,
            'ts_end': ts_end,
            'duration_ms': round(duration_ms, 3),
            'status_code': status_code,
            'rec_id': rec_id,
            'error_type': error_type,
            'error_msg': error_msg,
        }
        with results_lock:
            results.append(rec)


def save_report(records: List[Dict[str, Any]], total_elapsed: float,
                users: int, per_user: int, label: str,
                output_path: str) -> Dict[str, Any]:
    """汇总并保存压测报告."""
    success = sum(1 for r in records if r['status_code'] == 200)
    fail = len(records) - success
    durations = [r['duration_ms'] for r in records if r['duration_ms'] is not None]

    # 首次请求 vs 后续请求分析 (冷启动核心指标)
    first_requests = [r for r in records if r['iteration'] == 0]
    follow_requests = [r for r in records if r['iteration'] > 0]
    first_durations = [r['duration_ms'] for r in first_requests
                       if r['duration_ms'] is not None]
    follow_durations = [r['duration_ms'] for r in follow_requests
                        if r['duration_ms'] is not None]

    def _percentile(xs, p):
        if not xs:
            return 0.0
        xs_sorted = sorted(xs)
        k = (len(xs_sorted) - 1) * p / 100
        f, c = int(k), int(k) + 1
        if c >= len(xs_sorted):
            return xs_sorted[-1]
        return xs_sorted[f] + (xs_sorted[c] - xs_sorted[f]) * (k - f)

    first_avg = statistics.mean(first_durations) if first_durations else 0
    follow_avg = statistics.mean(follow_durations) if follow_durations else 0
    cold_start_ratio = (first_avg / follow_avg) if follow_avg > 0 else 0

    status_codes = Counter(r['status_code'] for r in records)
    error_types = Counter(r.get('error_type') for r in records
                          if r['status_code'] != 200)

    # 100ms 时间窗口分析
    if records:
        t0 = min(r['ts_start'] for r in records)
        windows = {}
        for r in records:
            offset_ms = (r['ts_start'] - t0) * 1000
            window_key = int(offset_ms // 100) * 100
            windows.setdefault(window_key, []).append(r['duration_ms'])
        window_stats = []
        for k in sorted(windows.keys()):
            ds = windows[k]
            window_stats.append({
                'window_ms': f'{k}-{k+100}',
                'count': len(ds),
                'avg_ms': round(statistics.mean(ds), 2),
                'max_ms': round(max(ds), 2),
                'p95_ms': round(_percentile(ds, 95), 2),
            })

    report = {
        'meta': {
            'base_url': BASE,
            'label': label,
            'users': users,
            'per_user': per_user,
            'total_requests': len(records),
            'wall_time_sec': round(total_elapsed, 3),
            'start_ts': records[0]['ts_start'] if records else None,
            'end_ts': records[-1]['ts_end'] if records else None,
            'thread_safe': True,
        },
        'cold_start': {
            'first_request_avg_ms': round(first_avg, 3),
            'first_request_p95_ms': round(_percentile(first_durations, 95), 3),
            'first_request_max_ms': round(max(first_durations) if first_durations else 0, 3),
            'follow_request_avg_ms': round(follow_avg, 3),
            'follow_request_p95_ms': round(_percentile(follow_durations, 95), 3),
            'follow_request_max_ms': round(max(follow_durations) if follow_durations else 0, 3),
            'cold_start_ratio': round(cold_start_ratio, 3),
            'verdict': (
                '✅ 优秀' if cold_start_ratio <= 1.5 else
                '🟢 良好' if cold_start_ratio <= 3.0 else
                '🟡 一般' if cold_start_ratio <= 5.0 else
                '🔴 冷启动严重'
            )
        },
        'summary': {
            'success_count': success,
            'fail_count': fail,
            'success_rate': round(success / len(records) * 100, 2) if records else 0,
            'avg_duration_ms': round(statistics.mean(durations), 3) if durations else 0,
            'median_duration_ms': round(statistics.median(durations), 3) if durations else 0,
            'p50_ms': round(_percentile(durations, 50), 3),
            'p95_ms': round(_percentile(durations, 95), 3),
            'p99_ms': round(_percentile(durations, 99), 3),
            'max_duration_ms': round(max(durations), 3) if durations else 0,
            'min_duration_ms': round(min(durations), 3) if durations else 0,
            'throughput_rps': round(len(records) / total_elapsed, 2) if total_elapsed > 0 else 0,
            'status_code_distribution': dict(status_codes),
            'error_count_by_type': dict(error_types),
        },
        'time_windows': window_stats,
        'records': records,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    log(f"Report saved to: {output_path}")
    return report


def verify_data_integrity(expected: int, user_tag: str) -> Dict[str, Any]:
    """验证 calc_id 唯一性和数据完整性."""
    r = requests.get(f"{BASE}/api/history?limit=500", timeout=10)
    if r.status_code != 200:
        return {'error': f'list returned {r.status_code}'}
    items = r.json()['data']['items']
    target = [it for it in items
              if (it.get('calc_id') or '').startswith(f'coldstart-{user_tag}-')]
    calc_ids = [it.get('calc_id') for it in target]
    counter = Counter(calc_ids)
    duplicates = {k: v for k, v in counter.items() if v > 1}
    return {
        'expected': expected,
        'actual': len(target),
        'unique_calc_ids': len(counter),
        'duplicates': duplicates,
        'integrity_ok': (
            len(target) == expected
            and len(duplicates) == 0
        ),
    }


def cleanup_coldstart_records(user_tag: str) -> int:
    """清理本次测试产生的记录."""
    r = requests.get(f"{BASE}/api/history?limit=500", timeout=10)
    if r.status_code != 200:
        return 0
    items = r.json()['data']['items']
    target_ids = [it['id'] for it in items
                  if (it.get('calc_id') or '').startswith(f'coldstart-{user_tag}-')]
    if target_ids:
        r = requests.delete(f"{BASE}/api/history?ids={','.join(map(str, target_ids))}")
        return len(target_ids) if r.status_code == 200 else 0
    return 0


def main():
    parser = argparse.ArgumentParser(description='冷启动效应压测 (10 用户)')
    parser.add_argument('--users', type=int, default=DEFAULT_USERS,
                        help=f'并发用户数 (默认 {DEFAULT_USERS})')
    parser.add_argument('--per-user', type=int, default=DEFAULT_PER_USER,
                        help=f'每用户请求数 (默认 {DEFAULT_PER_USER})')
    parser.add_argument('--label', type=str, default='optimized',
                        help='报告标签 (optimized / baseline)')
    parser.add_argument('--output', type=str, default=None,
                        help='报告输出路径 (默认自动生成)')
    parser.add_argument('--no-cleanup', action='store_true', help='不清理测试数据')
    args = parser.parse_args()

    if args.output is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"coldstart_report_{args.label}_{stamp}.json"

    user_tag = uuid.uuid4().hex[:8]
    total_expected = args.users * args.per_user

    log("=" * 70)
    log(f"冷启动效应压测 - /api/history [标签: {args.label}]")
    log("=" * 70)
    log(f"  Base URL:    {BASE}")
    log(f"  并发用户数:   {args.users}")
    log(f"  每用户请求:   {args.per_user}")
    log(f"  总请求数:     {total_expected}")
    log(f"  唯一标签:     {user_tag}")
    log(f"  报告输出:     {args.output}")
    log("")

    # 0. 服务可用性
    log("[0] 检查服务可用性")
    try:
        r = requests.get(f"{BASE}/api/history/stats", timeout=5)
        if r.status_code != 200:
            log(f"  ❌ 服务返回 {r.status_code}, 请先启动服务")
            log(f"     启动命令: cd c:\\Users\\Administrator\\机械计算小程序 ; python -m backend.app")
            return 1
        log(f"  ✅ 服务可用, 初始 total={r.json()['data']['total']}")
    except Exception as e:
        log(f"  ❌ 服务不可达: {e}")
        return 1

    # 1. 清理历史 coldstart- 数据
    if not args.no_cleanup:
        log("\n[1] 清理历史 coldstart- 记录")
        cleanup_coldstart_records(user_tag)

    # 2. 启动并发线程
    log(f"\n[2] 启动 {args.users} 个线程, 每线程 {args.per_user} 请求")
    log("    (使用 Barrier 确保所有线程同时发起首次请求, 模拟冷启动瞬间)")
    results: List[Dict[str, Any]] = []
    results_lock = threading.Lock()
    barrier = threading.Barrier(args.users)
    threads: List[threading.Thread] = []

    t_wall_start = time.time()
    for uid in range(args.users):
        t = threading.Thread(
            target=worker,
            args=(uid, args.per_user, results, results_lock, barrier, user_tag),
            name=f"User-{uid:02d}",
            daemon=True,
        )
        threads.append(t)
        t.start()

    log(f"  全部线程已启动, 等待完成...")
    for t in threads:
        t.join(timeout=60)
    t_wall_end = time.time()
    t_wall = t_wall_end - t_wall_start
    log(f"  ✅ 全部线程完成, wall_time={t_wall:.3f}s")

    # 3. 汇总
    log(f"\n[3] 汇总结果")
    success = sum(1 for r in results if r['status_code'] == 200)
    fail = len(results) - success
    durations = [r['duration_ms'] for r in results if r['duration_ms'] is not None]
    status_dist = Counter(r['status_code'] for r in results)
    error_types = Counter(r.get('error_type') for r in results
                          if r['status_code'] != 200)

    log(f"  成功:        {success}/{len(results)} "
        f"({success/len(results)*100:.1f}%)" if results else "  无结果")
    log(f"  失败:        {fail}")
    log(f"  状态码分布:   {dict(status_dist)}")
    log(f"  错误类型:     {dict(error_types) if error_types else '无'}")
    if durations:
        log(f"  响应时间:    min={min(durations):.2f}ms "
            f"avg={statistics.mean(durations):.2f}ms "
            f"max={max(durations):.2f}ms")
    log(f"  吞吐量:      {len(results) / t_wall:.1f} req/s")

    # 4. 冷启动分析
    log(f"\n[4] 冷启动分析 (核心指标)")
    first_reqs = [r for r in results if r['iteration'] == 0]
    follow_reqs = [r for r in results if r['iteration'] > 0]
    first_ds = [r['duration_ms'] for r in first_reqs if r['duration_ms'] is not None]
    follow_ds = [r['duration_ms'] for r in follow_reqs if r['duration_ms'] is not None]
    if first_ds and follow_ds:
        first_avg = statistics.mean(first_ds)
        follow_avg = statistics.mean(follow_ds)
        ratio = first_avg / follow_avg if follow_avg > 0 else 0
        log(f"  首次请求数:    {len(first_reqs)}")
        log(f"  首次 avg:      {first_avg:.2f}ms (max={max(first_ds):.2f}ms)")
        log(f"  后续 avg:      {follow_avg:.2f}ms (max={max(follow_ds):.2f}ms)")
        log(f"  冷启动比例:    {ratio:.2f}x")
        verdict = (
            '✅ 优秀 (≤1.5x)' if ratio <= 1.5 else
            '🟢 良好 (≤3.0x)' if ratio <= 3.0 else
            '🟡 一般 (≤5.0x)' if ratio <= 5.0 else
            '🔴 冷启动严重 (>5x)'
        )
        log(f"  评估:         {verdict}")

    # 5. 数据完整性
    log(f"\n[5] 数据完整性验证")
    integrity = verify_data_integrity(total_expected, user_tag)
    log(f"  期望:         {integrity.get('expected')}")
    log(f"  实际:         {integrity.get('actual')}")
    log(f"  唯一 calc_id: {integrity.get('unique_calc_ids')}")
    log(f"  重复:         {integrity.get('duplicates')}")
    log(f"  完整性:        {'✅ 通过' if integrity.get('integrity_ok') else '❌ 失败'}")

    # 6. 保存报告
    log(f"\n[6] 保存报告")
    report = save_report(results, t_wall, args.users, args.per_user,
                         args.label, args.output)

    # 7. 清理
    if not args.no_cleanup:
        log(f"\n[7] 清理测试数据")
        deleted = cleanup_coldstart_records(user_tag)
        log(f"  ✅ 清理 {deleted} 条记录")

    log("\n" + "=" * 70)
    log("结论")
    log("=" * 70)
    cs = report['cold_start']
    log(f"冷启动比例: {cs['cold_start_ratio']}x {cs['verdict']}")
    log(f"首次请求: {cs['first_request_avg_ms']}ms (P95={cs['first_request_p95_ms']}ms)")
    log(f"后续请求: {cs['follow_request_avg_ms']}ms (P95={cs['follow_request_p95_ms']}ms)")
    log(f"吞吐量: {report['summary']['throughput_rps']} req/s")
    log(f"完整性: {'✅ 通过' if integrity.get('integrity_ok') else '❌ 失败'}")

    return 0 if (integrity.get('integrity_ok') and success == total_expected) else 1


if __name__ == "__main__":
    sys.exit(main())
