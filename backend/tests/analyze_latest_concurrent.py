"""分析最新并发测试报告 (任务 3)"""
import json
import statistics
import sys
from collections import Counter, defaultdict


def analyze_report(report_path: str) -> None:
    with open(report_path, 'r', encoding='utf-8') as f:
        rpt = json.load(f)
    m = rpt['meta']
    s = rpt['summary']
    recs = rpt['records']

    print('=' * 60)
    print('并发测试报告分析 (15 用户 x 8 请求, 启用连接池)')
    print('=' * 60)
    print(f'报告: {report_path}')
    print(f'基本信息: {m["users"]} 用户 x {m["per_user"]} 请求 = {m["total_requests"]}')
    print(f'墙钟: {m["wall_time_sec"]}s')
    print(f'线程安全声明: {m["thread_safe"]}')
    print()
    print('--- 性能指标 ---')
    print(f'成功率: {s["success_rate"]}% ({s["success_count"]}/{m["total_requests"]})')
    print(f'吞吐量: {s["throughput_rps"]} req/s')
    print(f'平均: {s["avg_duration_ms"]}ms')
    print(f'中位数: {s["median_duration_ms"]}ms')
    print(f'P95: {s["p95_duration_ms"]}ms')
    print(f'最小/最大: {s["min_duration_ms"]}ms / {s["max_duration_ms"]}ms')
    print()
    print('--- 错误分布 ---')
    print(f'错误类型: {s["error_count_by_type"]}')
    print(f'状态码分布: {s["status_code_distribution"]}')
    print()

    # 响应时间分布
    durs = [r['duration_ms'] for r in recs]
    buckets = [0, 10, 50, 100, 200, 500, 1000, 9999]
    print('--- 响应时间分布 ---')
    for i in range(len(buckets) - 1):
        c = sum(1 for d in durs if buckets[i] <= d < buckets[i + 1])
        pct = round(c * 100 / len(durs), 1)
        bar = '#' * (c // 2)
        print(f'  [{buckets[i]:>4}ms, {buckets[i+1]:>4}ms): {c:>3} ({pct:>5.1f}%) {bar}')
    print()

    # 锁竞争分析: 响应时间 vs 用户
    print('--- 各用户响应时间统计 (锁竞争指标) ---')
    user_durs = defaultdict(list)
    for r in recs:
        user_durs[r['user_id']].append(r['duration_ms'])
    for uid in sorted(user_durs.keys()):
        ds = user_durs[uid]
        avg = round(statistics.mean(ds), 2)
        mx = round(max(ds), 2)
        sd = round(statistics.stdev(ds), 2) if len(ds) > 1 else 0
        print(f'  user_{uid:>2}: count={len(ds):>2} avg={avg:>6.2f}ms '
              f'max={mx:>6.2f}ms stdev={sd:>6.2f}ms')
    print()

    # 锁竞争特征: P95 与最大值的差距
    p95 = s['p95_duration_ms']
    mx = s['max_duration_ms']
    p99_p95_ratio = round(mx / p95, 2) if p95 > 0 else 0
    print('--- 锁竞争特征分析 ---')
    print(f'  P95 = {p95}ms')
    print(f'  Max = {mx}ms')
    print(f'  Max/P95 比 = {p99_p95_ratio}x')
    if p99_p95_ratio < 2:
        print('  ✅ 响应时间分布均匀, 无明显尾部锁等待')
    elif p99_p95_ratio < 5:
        print('  ⚠️  存在中等尾部延迟, 可能有偶发锁竞争')
    else:
        print('  ❌ 尾部延迟高, 存在明显锁竞争')

    # 锁竞争时间特征
    over_200ms = [r for r in recs if r['duration_ms'] > 200]
    if over_200ms:
        print(f'\n  > 200ms 的请求 ({len(over_200ms)} 个):')
        for r in over_200ms[:5]:
            print(f'    user_{r["user_id"]:>2} iter={r["iteration"]} '
                  f'{r["duration_ms"]:>6.2f}ms rec_id={r["rec_id"]}')
    print()

    # 与方案 A 对比 (基线)
    print('--- 与基线 (Task 3 120 并发无连接池) 对比 ---')
    print('  Task 3 报告关键指标 (来自 2026-06-05-task3-concurrent-analysis.md):')
    print('    - 120 并发: 平均 21.5ms, P95 51.3ms, 0 失败, 408.6 req/s')
    print()
    print('  Task 5 方案 B (本次, 15 用户 x 8 = 120 请求):')
    print(f'    - 15 并发线程: 平均 {s["avg_duration_ms"]}ms, '
          f'P95 {s["p95_duration_ms"]}ms, {s["fail_count"]} 失败, '
          f'{s["throughput_rps"]} req/s')
    print()
    print('  关键观察:')
    print('    - 总请求数相同 (120), 但并发模型不同 (Task 3: 120 并发线程; '
          'Task 5: 15 并发线程串行 8 次)')
    print('    - Task 5 模拟"15 用户长期使用"场景, 更接近生产实际')
    print('    - Task 3 模拟"突发 120 并发"场景, 接近最大压测')
    print()


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'concurrent_report_planB_20260605.json'
    analyze_report(path)
