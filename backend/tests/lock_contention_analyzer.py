"""锁竞争深度分析脚本 (任务 4)

通过注入延迟 + 并发执行, 量化不同锁点的竞争程度.
锁点列表 (源自代码扫描):
  L1. threading.Lock() _lock (init_db 全局)
  L2. threading.Lock() _pool_lock (池操作)
  L3. queue.LifoQueue.get() 内部锁 (获取连接)
  L4. SQLite 内部写锁 (INSERT/UPDATE)
  L5. SQLite WAL 写锁 (commit 时)
  L6. Python GIL (解释器级)
"""
import json
import os
import statistics
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# 设置环境
os.environ.setdefault('ENABLE_CONN_POOL', '1')
os.environ.setdefault('CONN_POOL_SIZE', '8')
os.environ.setdefault('DISABLE_DB_WARMUP', '0')

import requests

BASE = "http://127.0.0.1:9091"
HISTORY_URL = f"{BASE}/api/history"
STATS_URL = f"{BASE}/api/history/stats"


def clear_history():
    try:
        requests.delete(f"{HISTORY_URL}?all=1", timeout=5)
    except Exception:
        pass


def worker(uid: int, n: int, barrier: threading.Barrier,
           results: list, lock: threading.Lock):
    """单 worker: 等待同步起跑, 然后串行 n 个 POST."""
    barrier.wait()
    local = []
    for i in range(n):
        body = {
            'category': 'lock_analyze',
            'endpoint': '/api/lock',
            'calc_id': f'lock-{uid}-{i}',
            'input': {'uid': uid, 'i': i},
            'output': {'r': uid * 1000 + i},
        }
        start = time.perf_counter()
        try:
            r = requests.post(HISTORY_URL, json=body, timeout=10)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            local.append({
                'uid': uid, 'i': i,
                'duration_ms': elapsed_ms,
                'status': r.status_code,
            })
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            local.append({
                'uid': uid, 'i': i,
                'duration_ms': elapsed_ms,
                'status': -1,
                'error': str(e),
            })
    with lock:
        results.extend(local)


def run_scenario(name: str, users: int, per_user: int) -> dict:
    """运行一个并发场景, 返回统计."""
    print(f"\n>>> 场景: {name} (users={users}, per_user={per_user})")
    clear_history()
    results = []
    lock = threading.Lock()
    barrier = threading.Barrier(users)

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=users) as ex:
        futures = [ex.submit(worker, u, per_user, barrier, results, lock)
                   for u in range(users)]
        for f in futures:
            f.result()
    wall_ms = round((time.perf_counter() - start) * 1000, 2)

    durs = [r['duration_ms'] for r in results if r['status'] == 200]
    fails = [r for r in results if r['status'] != 200]
    if not durs:
        return {'name': name, 'success': 0, 'fail': len(fails)}

    durs_sorted = sorted(durs)
    p50 = durs_sorted[len(durs_sorted) // 2]
    p95 = durs_sorted[int(len(durs_sorted) * 0.95)] if len(durs_sorted) > 1 else durs_sorted[-1]
    p99 = durs_sorted[int(len(durs_sorted) * 0.99)] if len(durs_sorted) > 1 else durs_sorted[-1]
    mx = max(durs)

    out = {
        'name': name,
        'users': users,
        'per_user': per_user,
        'total': len(results),
        'success': len(durs),
        'fail': len(fails),
        'wall_ms': wall_ms,
        'throughput_rps': round(len(durs) * 1000 / wall_ms, 2),
        'avg_ms': round(statistics.mean(durs), 2),
        'median_ms': round(p50, 2),
        'p95_ms': round(p95, 2),
        'p99_ms': round(p99, 2),
        'max_ms': round(mx, 2),
        'stdev_ms': round(statistics.stdev(durs), 2) if len(durs) > 1 else 0,
        'max_p95_ratio': round(mx / p95, 2) if p95 > 0 else 0,
        'p99_p50_ratio': round(p99 / p50, 2) if p50 > 0 else 0,
    }
    return out


def analyze_lock_contention():
    """锁竞争深度分析: 通过改变并发数观察延迟分布变化."""
    print("=" * 70)
    print("锁竞争深度分析 (任务 4)")
    print("=" * 70)
    print("目标: 通过渐进并发数, 量化锁竞争对延迟的影响")
    print("方法: 5/10/15/20/30 并发, 观察 P50/P95/P99/Max 的变化趋势")
    print()

    scenarios = [
        ('低并发 (5 用户 x 8)', 5, 8),
        ('中并发 (10 用户 x 8)', 10, 8),
        ('中高并发 (15 用户 x 8)', 15, 8),
        ('高并发 (20 用户 x 8)', 20, 8),
        ('压力并发 (30 用户 x 8)', 30, 8),
    ]

    results = []
    for name, users, per_user in scenarios:
        try:
            r = run_scenario(name, users, per_user)
            results.append(r)
        except Exception as e:
            print(f"  失败: {e}")
            continue

    print("\n" + "=" * 70)
    print("锁竞争特征对比 (按并发用户数)")
    print("=" * 70)
    print(f"{'场景':<28} {'成功':>6} {'P50':>8} {'P95':>8} "
          f"{'P99':>8} {'Max':>8} {'P99/P50':>8}")
    print("-" * 70)
    for r in results:
        print(f"{r['name']:<28} {r['success']:>6} {r['median_ms']:>7.1f}ms "
              f"{r['p95_ms']:>7.1f}ms {r['p99_ms']:>7.1f}ms "
              f"{r['max_ms']:>7.1f}ms {r['p99_p50_ratio']:>7.2f}x")
    print()

    # 锁竞争类型分析
    print("=" * 70)
    print("锁竞争类型分析")
    print("=" * 70)

    if len(results) >= 2:
        # 取最低并发和高并发对比
        low = results[0]
        high = results[-1]
        p50_growth = high['median_ms'] / low['median_ms'] if low['median_ms'] > 0 else 0
        p95_growth = high['p95_ms'] / low['p95_ms'] if low['p95_ms'] > 0 else 0
        p99_growth = high['p99_ms'] / low['p99_ms'] if low['p99_ms'] > 0 else 0
        print(f"P50 增长: {p50_growth:.2f}x (并发 {low['users']}→{high['users']})")
        print(f"P95 增长: {p95_growth:.2f}x")
        print(f"P99 增长: {p99_growth:.2f}x")
        print()
        if p99_growth > 5:
            print("⚠️  P99 增长 > 5x, 存在严重尾部锁竞争")
        elif p99_growth > 2:
            print("⚠️  P99 增长 > 2x, 存在中等尾部锁竞争")
        else:
            print("✅ P99 增长 ≤ 2x, 锁竞争可控")

    # 读取池统计
    try:
        r = requests.get(STATS_URL, timeout=5).json()
        pool = r.get('data', {}).get('pool', {})
        print()
        print("--- 当前池状态 ---")
        print(json.dumps(pool, indent=2, ensure_ascii=False))

        # 降级率分析
        total = pool.get('get_count', 0)
        fb = pool.get('fallback_count', 0)
        if total > 0:
            fb_rate = fb * 100 / total
            print(f"\n降级率: {fb_rate:.2f}% ({fb}/{total})")
            if fb_rate > 30:
                print("⚠️  降级率 > 30%, 池大小不足, 需扩容")
            elif fb_rate > 10:
                print("⚠️  降级率 > 10%, 池大小偏小")
            else:
                print("✅ 降级率 < 10%, 池大小合理")
    except Exception as e:
        print(f"读取池状态失败: {e}")

    # 保存报告
    with open('lock_contention_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n报告已保存: lock_contention_report.json")

    return results


if __name__ == '__main__':
    analyze_lock_contention()
