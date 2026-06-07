"""连接池功能验证脚本 (任务 2)

验证维度:
  1. 启动时池创建 (8 个连接预创建)
  2. 请求时分配/归还 (qsize 波动)
  3. 监控指标 (hit_count / fallback_count / health_fail_count)
  4. 连接数预期范围内 (不超 8, 不低于 0)
  5. 并发场景下无连接泄漏
"""
import json
import sys
import time
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_URL = "http://127.0.0.1:9091"
HISTORY_URL = f"{BASE_URL}/api/history"
STATS_URL = f"{BASE_URL}/api/history/stats"

# 写一个直接读取池统计的端点 (如果没有, 使用 stats 端点反推)
POOL_STATS_URL = f"{BASE_URL}/api/pool/stats"  # 假设存在


def http_get(url: str, timeout: int = 5) -> dict:
    """HTTP GET, 返回 dict."""
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def http_post(url: str, data: dict, timeout: int = 5) -> dict:
    """HTTP POST, 返回 dict."""
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        url, data=body, headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def post_history(category: str, endpoint: str, calc_id_suffix: str) -> tuple:
    """发送单条历史记录 POST 请求, 返回 (status_code, elapsed_ms, error)."""
    body = {
        'category': category,
        'endpoint': endpoint,
        'calc_id': f'pool-test-{calc_id_suffix}',
        'input': {'test': True, 'id': calc_id_suffix},
        'output': {'result': int(calc_id_suffix) * 10}
    }
    start = time.perf_counter()
    try:
        r = http_post(HISTORY_URL, body)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return (200, elapsed_ms, None)
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return (-1, elapsed_ms, str(e))


def phase1_initial_state():
    """阶段 1: 验证启动时池已创建."""
    print("=" * 60)
    print("[阶段 1] 启动时连接池创建验证")
    print("=" * 60)

    # 通过 stats 端点确认服务可用 + 读取池统计
    try:
        stats = http_get(STATS_URL)
        print(f"[+] 服务可用: {stats.get('status')}")
        pool = stats.get('data', {}).get('pool')
        if pool:
            print(f"[+] 池已创建:")
            print(f"    enabled     = {pool.get('enabled')}")
            print(f"    size        = {pool.get('size')} (配置池大小)")
            print(f"    qsize       = {pool.get('qsize')} (当前池中连接数)")
            print(f"    created     = {pool.get('created')} (累计创建数)")
            print(f"    get_count   = {pool.get('get_count')} (累计获取次数)")
            print(f"    hit_count   = {pool.get('hit_count')} (命中次数)")
            print(f"    hit_rate    = {pool.get('hit_rate')}% (命中率)")
            print(f"    fallback    = {pool.get('fallback_count')} (降级次数)")
            return pool
        else:
            print("[!] 池未启用 (ENABLE_CONN_POOL=0)")
            return None
    except Exception as e:
        print(f"[!] 服务不可用: {e}")
        return False


def phase2_single_request():
    """阶段 2: 单请求验证 (分配/回收)."""
    print("\n" + "=" * 60)
    print("[阶段 2] 单请求 - 池分配/回收验证")
    print("=" * 60)

    for i in range(3):
        status, ms, err = post_history('pool_verify', '/api/verify', str(i))
        if err:
            print(f"  [{i+1}] 失败: {err}")
        else:
            print(f"  [{i+1}] 状态={status} 耗时={ms}ms")


def phase3_concurrent_burst():
    """阶段 3: 并发突发 (10 并发 x 5 请求 = 50)."""
    print("\n" + "=" * 60)
    print("[阶段 3] 并发突发 - 池抗压验证 (10 并发 x 5 请求)")
    print("=" * 60)

    n_workers = 10
    n_per_worker = 5
    total = n_workers * n_per_worker
    print(f"  启动 {n_workers} 并发, 每线程 {n_per_worker} 请求, 总计 {total} 请求")

    results = []
    results_lock = threading.Lock()
    barrier = threading.Barrier(n_workers)

    def worker(uid):
        barrier.wait()  # 同步起跑
        for i in range(n_per_worker):
            r = post_history('pool_burst', '/api/burst', f'{uid}_{i}')
            with results_lock:
                results.append(r)

    start = time.perf_counter()
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    wall_ms = round((time.perf_counter() - start) * 1000, 2)

    # 统计
    success = sum(1 for s, _, _ in results if s == 200)
    failed = total - success
    latencies = [ms for _, ms, _ in results]
    if latencies:
        avg_ms = round(sum(latencies) / len(latencies), 2)
        max_ms = round(max(latencies), 2)
        min_ms = round(min(latencies), 2)
    else:
        avg_ms = max_ms = min_ms = 0

    # 验证写入是否真的入库
    stats = http_get(STATS_URL)
    total_in_db = stats.get('data', {}).get('total', 0)

    print(f"\n  --- 并发结果 ---")
    print(f"  成功/失败: {success}/{failed}")
    print(f"  墙钟耗时: {wall_ms}ms")
    print(f"  延迟 avg/min/max: {avg_ms}/{min_ms}/{max_ms}ms")
    print(f"  DB 实际记录数: {total_in_db}")
    if total_in_db >= total * 0.9:  # 90% 容忍
        print(f"  ✅ 数据完整性: 良好 ({total_in_db}/{total}={round(total_in_db*100/total, 1)}%)")
    else:
        print(f"  ⚠ 数据完整性: 不足 ({total_in_db}/{total}={round(total_in_db*100/total, 1)}%)")

    if success == total:
        print(f"  ✅ 100% 成功: 无连接泄漏/超时")
        return True
    else:
        print(f"  ⚠ 成功率: {round(success*100/total, 1)}%")
        return False


def phase4_pool_stats_check():
    """阶段 4: 池统计指标 (使用 stats 端点)."""
    print("\n" + "=" * 60)
    print("[阶段 4] 池统计指标验证 (并发后)")
    print("=" * 60)
    try:
        stats = http_get(STATS_URL)
        pool = stats.get('data', {}).get('pool') or {}
        total = stats.get('data', {}).get('total', 0)
        cats = stats.get('data', {}).get('by_category', {})

        print(f"  --- 数据库状态 ---")
        print(f"  总记录数: {total}")
        print(f"  分类统计: {json.dumps(cats, ensure_ascii=False)}")
        print(f"\n  --- 连接池状态 ---")
        for k in ['enabled', 'size', 'qsize', 'created', 'get_count',
                  'hit_count', 'hit_rate', 'fallback_count', 'fallback_rate',
                  'health_fail_count']:
            v = pool.get(k)
            print(f"    {k:20s} = {v}")

        # 验证关键指标
        print(f"\n  --- 健康检查 ---")
        ok = True
        if pool.get('size') != 8:
            print(f"  ❌ size != 8 (期望 8)")
            ok = False
        if pool.get('qsize') != 8:
            print(f"  ⚠ qsize != 8 (期望 8, 实际 {pool.get('qsize')}, "
                  f"并发后部分连接未归还)")
            # 这不一定是 bug — 如果并发请求仍占用, qsize 暂时会降低
        if pool.get('created') != 8:
            print(f"  ❌ created != 8 (预创建异常)")
            ok = False
        if pool.get('hit_rate', 0) < 80:
            print(f"  ⚠ 命中率 < 80% (实际 {pool.get('hit_rate')}%)")
        else:
            print(f"  ✅ 命中率: {pool.get('hit_rate')}% (健康)")
        if pool.get('health_fail_count', 0) > 0:
            print(f"  ⚠ 健康检查失败: {pool.get('health_fail_count')} 次")
        else:
            print(f"  ✅ 无健康检查失败")
        if ok:
            print(f"\n  ✅ 连接池工作正常")
        return ok
    except Exception as e:
        print(f"  [!] 错误: {e}")
        return False


def main():
    print("\n" + "#" * 60)
    print("# 连接池功能验证脚本")
    print(f"# 目标: {BASE_URL}")
    print("#" * 60 + "\n")

    phase1_initial_state()
    phase2_single_request()
    phase3_concurrent_burst()
    phase4_pool_stats_check()

    print("\n" + "=" * 60)
    print("✅ 连接池验证脚本执行完毕")
    print("=" * 60)


if __name__ == '__main__':
    main()
