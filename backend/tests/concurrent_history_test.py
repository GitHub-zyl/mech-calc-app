"""并发写测试脚本 - 验证 /api/history 数据库锁机制

测试目标:
- 模拟 N 个用户同时写入历史数据
- 验证 SQLite WAL 模式 + 短连接机制能否防止数据竞争
- 记录每个请求的状态码、响应时间、异常
- 最终统计成功率、平均/最大响应时间、异常分布

使用:
    python -m backend.tests.concurrent_history_test
    python -m backend.tests.concurrent_history_test --users 20 --per-user 5
    python -m backend.tests.concurrent_history_test --users 10 --output report.json
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
from typing import Dict, List, Any

# UTF-8 输出
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import requests

BASE = "http://127.0.0.1:9091"


def _ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log(msg):
    try:
        print(f"[{_ts()}] {msg}", flush=True)
    except UnicodeEncodeError:
        safe = msg.encode('gbk', errors='replace').decode('gbk', errors='replace')
        print(f"[{_ts()}] {safe}", flush=True)


def save_result(records: List[Dict[str, Any]], total_elapsed: float,
                users: int, per_user: int, output_path: str):
    """保存测试报告为 JSON."""
    status_codes = Counter(r['status_code'] for r in records)
    success = sum(1 for r in records if r['status_code'] == 200)
    fail = len(records) - success
    durations = [r['duration_ms'] for r in records if r['duration_ms'] is not None]

    report = {
        'meta': {
            'base_url': BASE,
            'users': users,
            'per_user': per_user,
            'total_requests': len(records),
            'wall_time_sec': round(total_elapsed, 3),
            'start_ts': records[0]['ts_start'] if records else None,
            'end_ts': records[-1]['ts_end'] if records else None,
            'thread_safe': True,
        },
        'summary': {
            'success_count': success,
            'fail_count': fail,
            'success_rate': round(success / len(records) * 100, 2) if records else 0,
            'avg_duration_ms': round(statistics.mean(durations), 3) if durations else 0,
            'median_duration_ms': round(statistics.median(durations), 3) if durations else 0,
            'p95_duration_ms': round(statistics.quantiles(durations, n=20)[-1], 3) if len(durations) >= 5 else 0,
            'max_duration_ms': round(max(durations), 3) if durations else 0,
            'min_duration_ms': round(min(durations), 3) if durations else 0,
            'throughput_rps': round(len(records) / total_elapsed, 2) if total_elapsed > 0 else 0,
            'status_code_distribution': dict(status_codes),
            'error_count_by_type': dict(Counter(
                r.get('error_type', 'none') for r in records if r['status_code'] != 200
            )),
        },
        'records': records,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    log(f"Report saved to: {output_path}")


def worker(user_id: int, per_user: int, results: List[Dict[str, Any]],
           start_barrier: threading.Barrier, user_tag: str):
    """单个用户的工作线程. 写入 per_user 条记录."""
    thread_name = f"user_{user_id}"
    for i in range(per_user):
        # 等待所有线程就绪, 最大化并发瞬间
        if i == 0:
            start_barrier.wait()
        payload = {
            'category': f'{user_tag}_cat',
            'endpoint': f'/api/concurrent/test/{user_id}/{i}',
            'calc_id': f'concurrent-{user_id}-{i}',
            'input': {
                'user_id': user_id,
                'iteration': i,
                'thread_id': threading.get_ident(),
                'timestamp': time.time(),
            },
            'output': {
                'result': user_id * 1000 + i,
                'thread_name': thread_name,
            },
            'duration_ms': 0.5 + (i * 0.1),
        }
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

        results.append({
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
        })


def verify_count(expected: int) -> Dict[str, Any]:
    """验证数据库中的总记录数."""
    r = requests.get(f"{BASE}/api/history/stats")
    if r.status_code != 200:
        return {'error': f'stats returned {r.status_code}'}
    return r.json()['data']


def verify_no_duplicates() -> Dict[str, Any]:
    """验证 calc_id 唯一性 (防止写覆盖)."""
    r = requests.get(f"{BASE}/api/history?limit=500")
    if r.status_code != 200:
        return {'error': f'list returned {r.status_code}'}
    items = r.json()['data']['items']
    calc_ids = [it.get('calc_id') for it in items if it.get('calc_id', '').startswith('concurrent-')]
    counter = Counter(calc_ids)
    duplicates = {k: v for k, v in counter.items() if v > 1}
    return {
        'total_concurrent_records': len(calc_ids),
        'unique_calc_ids': len(counter),
        'duplicates': duplicates,
    }


def cleanup_concurrent_records():
    """清理测试产生的记录 (calc_id 以 concurrent- 开头)."""
    r = requests.get(f"{BASE}/api/history?limit=500")
    if r.status_code != 200:
        return
    items = r.json()['data']['items']
    target_ids = [it['id'] for it in items if (it.get('calc_id') or '').startswith('concurrent-')]
    if target_ids:
        r = requests.delete(f"{BASE}/api/history?ids={','.join(map(str, target_ids))}")
        log(f"Cleanup: deleted {len(target_ids)} concurrent records (status={r.status_code})")


def main():
    parser = argparse.ArgumentParser(description='并发写入测试')
    parser.add_argument('--users', type=int, default=10, help='并发用户数 (默认 10)')
    parser.add_argument('--per-user', type=int, default=5, help='每用户请求数 (默认 5)')
    parser.add_argument('--output', type=str, default=None, help='报告输出路径 (默认自动生成)')
    parser.add_argument('--no-cleanup', action='store_true', help='不清理测试数据')
    args = parser.parse_args()

    if args.output is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"concurrent_report_{stamp}.json"

    user_tag = f"ct{uuid.uuid4().hex[:6]}"  # 唯一标签, 避免跨次测试污染
    total_expected = args.users * args.per_user

    log("=" * 70)
    log(f"Task 4: 并发写测试 - /api/history")
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
            log(f"  服务返回 {r.status_code}, 请先启动服务 (python -m backend.app)")
            return 1
        log(f"  服务可用, 初始 total={r.json()['data']['total']}")
    except Exception as e:
        log(f"  服务不可达: {e}")
        log(f"  请先启动: cd c:\\Users\\Administrator\\机械计算小程序 && python -m backend.app")
        return 1

    # 1. 清理历史 concurrent- 数据
    if not args.no_cleanup:
        log("\n[1] 清理历史 concurrent- 记录")
        cleanup_concurrent_records()

    # 2. 启动并发线程
    log(f"\n[2] 启动 {args.users} 个线程, 每线程 {args.per_user} 请求")
    results: List[Dict[str, Any]] = []
    results_lock = threading.Lock()
    barrier = threading.Barrier(args.users)
    threads: List[threading.Thread] = []

    t_wall_start = time.time()
    for uid in range(args.users):
        t = threading.Thread(
            target=worker,
            args=(uid, args.per_user, results, barrier, user_tag),
            name=f"User-{uid:02d}",
            daemon=True,
        )
        threads.append(t)
        t.start()

    log(f"  全部线程已启动, 等待完成...")
    for t in threads:
        t.join(timeout=30)
    t_wall_end = time.time()
    t_wall = t_wall_end - t_wall_start
    log(f"  全部线程完成, wall_time={t_wall:.3f}s")

    # 3. 汇总
    log(f"\n[3] 汇总结果")
    success = sum(1 for r in records_iter(results) if r['status_code'] == 200)
    fail = len(results) - success
    durations = [r['duration_ms'] for r in records_iter(results) if r['duration_ms'] is not None]
    status_dist = Counter(r['status_code'] for r in records_iter(results))
    error_types = Counter(r.get('error_type') for r in records_iter(results) if r['status_code'] != 200)

    log(f"  成功:        {success}/{len(results)} ({success/len(results)*100:.1f}%)" if results else "  无结果")
    log(f"  失败:        {fail}")
    log(f"  状态码分布:   {dict(status_dist)}")
    log(f"  错误类型:     {dict(error_types) if error_types else '无'}")
    if durations:
        log(f"  响应时间:    min={min(durations):.2f}ms median={statistics.median(durations):.2f}ms "
            f"avg={statistics.mean(durations):.2f}ms max={max(durations):.2f}ms")
    log(f"  吞吐量:      {len(results) / t_wall:.1f} req/s")

    # 4. 数据完整性验证
    log(f"\n[4] 数据完整性验证")
    stats = verify_count(total_expected)
    log(f"  stats: {stats}")
    dup = verify_no_duplicates()
    log(f"  concurrent- 记录: {dup.get('total_concurrent_records', 0)}")
    log(f"  唯一 calc_id:     {dup.get('unique_calc_ids', 0)}")
    log(f"  重复:             {dup.get('duplicates', {})}")

    integrity_ok = (
        dup.get('total_concurrent_records', 0) == total_expected
        and len(dup.get('duplicates', {})) == 0
        and success == total_expected
    )
    log(f"\n  数据完整性: {'✅ 通过' if integrity_ok else '❌ 失败'}")

    # 5. 锁机制验证
    log(f"\n[5] 锁机制验证")
    lock_ok = success == total_expected
    log(f"  写入成功率 100%: {'✅' if lock_ok else '❌'} ({success}/{total_expected})")
    log(f"  无 calc_id 重复: {'✅' if not dup.get('duplicates') else '❌ ' + str(dup.get('duplicates'))}")
    log(f"  无连接超时:      {'✅' if 'timeout' not in error_types else '❌'}")

    # 6. 保存报告
    log(f"\n[6] 保存报告")
    save_result(list(results), t_wall, args.users, args.per_user, args.output)

    # 7. 清理
    if not args.no_cleanup:
        log(f"\n[7] 清理测试数据")
        cleanup_concurrent_records()

    log("\n" + "=" * 70)
    log("结论")
    log("=" * 70)
    if integrity_ok:
        log(f"✅ 通过: {args.users} 个并发用户同时写入 {args.per_user} 条记录, "
            f"共 {total_expected} 条, 全部成功, 无数据竞争")
        log("   数据库锁机制 (WAL 模式 + 短连接) 有效防止了数据不一致问题")
        return 0
    else:
        log("❌ 失败: 数据完整性或锁机制存在异常")
        return 1


def records_iter(results: List[Dict[str, Any]]):
    """兼容 results 可能在并发中被修改的情况: 遍历快照."""
    return list(results)


if __name__ == "__main__":
    sys.exit(main())
