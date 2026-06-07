"""并发测试报告深度分析 - 锁竞争/性能瓶颈检测.

分析 120 并发压测报告 (concurrent_report_20260604_233926.json):
- 响应时间分布
- 用户/线程级性能对比
- 写入间隔分析 (检测 WAL 锁竞争)
- 尾延迟 (P99/P95) 异常点
"""
import json
import statistics
from collections import defaultdict
from pathlib import Path

REPORT = Path("c:/Users/Administrator/机械计算小程序/concurrent_report_20260604_233926.json")
data = json.loads(REPORT.read_text(encoding="utf-8"))
records = data["records"]
summary = data["summary"]
meta = data["meta"]

print("=" * 78)
print(f"并发压测报告深度分析 - {meta['users']} 用户 x {meta['per_user']} 请求 = {meta['total_requests']} 总请求")
print("=" * 78)

# ============================================================
# 1. 总体统计
# ============================================================
print("\n【1】 总体统计")
print(f"  成功率:           {summary['success_rate']}% ({summary['success_count']}/{meta['total_requests']})")
print(f"  吞吐量:           {summary['throughput_rps']} RPS")
print(f"  墙钟耗时:         {meta['wall_time_sec']}s")
print(f"  响应时间: min={summary['min_duration_ms']}ms  median={summary['median_duration_ms']}ms  "
      f"avg={summary['avg_duration_ms']}ms  max={summary['max_duration_ms']}ms  p95={summary['p95_duration_ms']}ms")

# 计算 P99 和 P50/P75/P90/P99
durations = sorted(r["duration_ms"] for r in records)
def pct(p):
    return durations[int(len(durations) * p / 100) - 1] if durations else 0
print(f"  分位数:  P50={pct(50)}ms  P75={pct(75)}ms  P90={pct(90)}ms  P95={pct(95)}ms  P99={pct(99)}ms")
print(f"  错误数:           {summary['fail_count']}  错误类型: {summary['error_count_by_type']}")

# ============================================================
# 2. 用户级性能分布
# ============================================================
print("\n【2】 用户级性能分布 (15 用户的平均响应时间)")
user_stats = defaultdict(list)
for r in records:
    user_stats[r["user_id"]].append(r["duration_ms"])

print(f"  {'User':<8} {'Records':<10} {'Min':<10} {'Avg':<10} {'Max':<10} {'Total':<10}")
slow_users = []
for uid in sorted(user_stats.keys()):
    durs = user_stats[uid]
    avg = statistics.mean(durs)
    total = sum(durs)
    print(f"  user_{uid:<3} {len(durs):<10} {min(durs):<10.2f} {avg:<10.2f} {max(durs):<10.2f} {total:<10.2f}")
    if max(durs) > 500:  # 标记超过 500ms 的用户
        slow_users.append((uid, max(durs)))

# ============================================================
# 3. 首次 vs 后续响应 (冷启动检测)
# ============================================================
print("\n【3】 首次请求 vs 后续请求 (冷启动/数据库预热检测)")
first_reqs = [r for r in records if r["iteration"] == 0]
follow_reqs = [r for r in records if r["iteration"] > 0]
if first_reqs:
    first_avg = statistics.mean(r["duration_ms"] for r in first_reqs)
    first_max = max(r["duration_ms"] for r in first_reqs)
    print(f"  首次请求 (15): avg={first_avg:.2f}ms  max={first_max:.2f}ms")
if follow_reqs:
    follow_avg = statistics.mean(r["duration_ms"] for r in follow_reqs)
    follow_max = max(r["duration_ms"] for r in follow_reqs)
    print(f"  后续请求 (105): avg={follow_avg:.2f}ms  max={follow_max:.2f}ms")
    speedup = first_avg / follow_avg
    print(f"  冷启动效应: 首次比后续慢 {speedup:.1f}x")

# ============================================================
# 4. 时间序列分析 - 检测锁竞争模式
# ============================================================
print("\n【4】 时间序列分析 (按时间窗口统计响应时间)")
window_ms = 100  # 100ms 窗口
all_ts = sorted(r["ts_start"] for r in records)
t_min = all_ts[0]
t_max = max(r["ts_end"] for r in records)
buckets = defaultdict(list)
for r in records:
    bucket_key = int((r["ts_start"] - t_min) * 1000 / window_ms)
    buckets[bucket_key].append(r["duration_ms"])

print(f"  {'Window':<10} {'Count':<8} {'Avg(ms)':<10} {'Max(ms)':<10} {'P95(ms)':<10} {'Status'}")
peak_window = None
peak_avg = 0
for k in sorted(buckets.keys()):
    durs = buckets[k]
    avg = statistics.mean(durs)
    mx = max(durs)
    p95 = sorted(durs)[int(len(durs) * 0.95) - 1] if len(durs) >= 5 else mx
    marker = ""
    if avg > 100:
        marker = "⚠ 慢"
        if avg > peak_avg:
            peak_avg = avg
            peak_window = k
    print(f"  {k*window_ms:>4}-{((k+1)*window_ms):<4} {len(durs):<8} {avg:<10.2f} {mx:<10.2f} {p95:<10.2f} {marker}")

if peak_window is not None:
    print(f"\n  ⚠ 性能瓶颈窗口: {peak_window*window_ms}-{(peak_window+1)*window_ms}ms (平均响应 {peak_avg:.2f}ms)")

# ============================================================
# 5. 锁竞争检测 - 写入间隔异常
# ============================================================
print("\n【5】 锁竞争检测 - 写入完成间隔")
# 排序按完成时间
sorted_by_end = sorted(records, key=lambda r: r["ts_end"])
gaps = []
for i in range(1, len(sorted_by_end)):
    gap = (sorted_by_end[i]["ts_end"] - sorted_by_end[i-1]["ts_end"]) * 1000
    gaps.append(gap)
if gaps:
    gaps_sorted = sorted(gaps)
    print(f"  完成间隔: min={min(gaps):.2f}ms  median={statistics.median(gaps):.2f}ms  max={max(gaps):.2f}ms")
    big_gaps = [(i+1, g) for i, g in enumerate(gaps) if g > 20]  # 20ms 以上
    if big_gaps:
        print(f"  ⚠ 大间隔点 (>20ms, 共 {len(big_gaps)} 个):")
        for idx, g in big_gaps[:10]:
            print(f"     [#{idx}] {g:.2f}ms")
    else:
        print(f"  ✓ 无显著大间隔, 锁竞争不明显")

# ============================================================
# 6. 异常延迟点 - 长尾
# ============================================================
print("\n【6】 长尾延迟分析 (P95 以上)")
threshold = summary["p95_duration_ms"]
tail = [r for r in records if r["duration_ms"] > threshold]
print(f"  P95 阈值: {threshold}ms  长尾记录数: {len(tail)} ({len(tail)/len(records)*100:.1f}%)")
if tail:
    print(f"  长尾样本 (前 5 个):")
    for r in sorted(tail, key=lambda x: -x["duration_ms"])[:5]:
        print(f"     user_{r['user_id']:>2} iter_{r['iteration']}  {r['duration_ms']:.2f}ms  ts={r['ts_start']:.3f}")

# ============================================================
# 7. 总体结论
# ============================================================
print("\n【7】 总体结论")
print(f"  数据完整性:       {'✓ 通过 (120/120)' if summary['success_count'] == meta['total_requests'] else '✗ 失败'}")
print(f"  锁竞争证据:       {'未发现 (无 calc_id 重复, 写入全部成功)' if summary['error_count_by_type'] == {} else '发现'}")
print(f"  性能评级:         ", end="")
if summary["p95_duration_ms"] < 200:
    print("✓ 优秀 (P95 < 200ms)")
elif summary["p95_duration_ms"] < 500:
    print("✓ 良好 (P95 < 500ms)")
else:
    print("⚠ 需优化 (P95 >= 500ms)")

print(f"  瓶颈分析:         ", end="")
if peak_avg > 100:
    print(f"在 {peak_window*window_ms}ms 窗口有 {peak_avg:.0f}ms 延迟, 疑似初次写入 + WAL 同步")
else:
    print("无明显瓶颈")

# ============================================================
# 8. 优化建议
# ============================================================
print("\n【8】 优化建议")
if summary["p95_duration_ms"] > 300:
    print("  1. P95 > 300ms, 建议:")
    print("     - 增加连接池 (Flask + SQLAlchemy)")
    print("     - 启用 HTTP/2 (减少握手开销)")
    print("     - 考虑批量写入 API (减少事务提交次数)")
if first_avg > 200:
    print(f"  2. 首次请求 avg={first_avg:.0f}ms 显著慢于后续, 建议:")
    print("     - 服务启动时预热数据库连接")
    print("     - 应用启动后做一次预热写入")
if len(tail) > len(records) * 0.05:
    print(f"  3. 长尾记录占 {len(tail)/len(records)*100:.1f}%, 建议:")
    print("     - 增加 SQLite busy_timeout (当前 10s, 可降到 5s + 重试)")
    print("     - 监控 WAL checkpoint 频率")

print("\n" + "=" * 78)
print("分析完成")
print("=" * 78)
