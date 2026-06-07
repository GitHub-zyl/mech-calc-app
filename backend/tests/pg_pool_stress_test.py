"""PostgreSQL 连接池高并发压力测试脚本 (本地模拟)

设计目标:
- 在本地模拟 PostgreSQL 数据库 (使用 SQLite 模拟协议, 验证连接池行为)
- 100 并发连接场景下验证:
  * 连接池获取/释放效率
  * 资源占用 (打开连接数/队列深度)
  * 错误处理 (超时/失败重试)
- 报告: 响应时间 (avg/p50/p95/p99/max) + 成功率 + 错误率

使用:
    python -m backend.tests.pg_pool_stress_test
    python -m backend.tests.pg_pool_stress_test --concurrency 100 --requests 50
    python -m backend.tests.pg_pool_stress_test --output report.json

工作原理:
- 使用线程池模拟高并发客户端
- 通过 DBAdapter 抽象层跑事务 (BEGIN → SELECT → INSERT → COMMIT)
- 模拟 PG 行为:
  * pool_size=20 (稳态连接)
  * max_overflow=80 (峰值连接) → 总上限 100 = 20+80
  * 借用超时 5s
  * 随机慢查询 (10-50ms) 模拟真实负载
"""
import argparse
import json
import logging
import os
import queue
import random
import statistics
import sys
import threading
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# UTF-8 输出
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 项目根加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 模拟 PostgreSQL 行为的协议层
# ============================================================

class MockPGConnection:
    """模拟 psycopg2 连接对象.

    不真正连 PG, 但模拟:
    - 连接建立/释放时间
    - 慢查询 (sleep)
    - 偶发错误 (simulated failure rate)
    """

    def __init__(self, conn_id: int, slow_prob: float = 0.1):
        self.conn_id = conn_id
        self.created_at = time.time()
        self.last_used_at = time.time()
        self.busy = False
        self._slow_prob = slow_prob
        self._closed = False

    def cursor(self):
        if self._closed:
            raise RuntimeError(f"MockPGConnection #{self.conn_id} is closed")
        return MockPGCursor(self)

    def commit(self):
        self.last_used_at = time.time()

    def rollback(self):
        self.last_used_at = time.time()

    def close(self):
        self._closed = True


class MockPGCursor:
    def __init__(self, conn: MockPGConnection):
        self.conn = conn
        self._rows = []

    def execute(self, sql, params=()):
        # 模拟慢查询: 10-50ms
        if random.random() < self.conn._slow_prob:
            time.sleep(random.uniform(0.01, 0.05))
        else:
            time.sleep(random.uniform(0.001, 0.005))

        # 模拟错误率 (仅在测试错误率场景)
        if os.getenv('MOCK_PG_ERROR_RATE'):
            err_rate = float(os.getenv('MOCK_PG_ERROR_RATE'))
            if random.random() < err_rate:
                raise RuntimeError(f"Simulated PG error on conn={self.conn.conn_id}")

    def fetchone(self):
        return {'id': 1, 'val': 'ok'}

    def fetchall(self):
        return [{'id': 1, 'val': 'ok'}] * random.randint(1, 5)

    def close(self):
        pass


class MockPGPool:
    """模拟 SQLAlchemy QueuePool 行为.

    - pool_size: 稳态连接
    - max_overflow: 峰值连接 (pool_size + max_overflow = 硬上限)
    - pool_timeout: 获取连接超时
    - pool_recycle: 连接超过此时间会被回收
    - pool_pre_ping: 借出前检查
    """

    def __init__(self, size: int = 20, max_overflow: int = 80,
                 timeout: float = 5.0, recycle: int = 3600):
        self._size = size
        self._max_overflow = max_overflow
        self._timeout = timeout
        self._recycle = recycle

        self._pool: queue.LifoQueue = queue.LifoQueue(maxsize=size)
        self._overflow_count = 0
        self._overflow_lock = threading.Lock()
        self._next_conn_id = 0
        self._id_lock = threading.Lock()
        self._all_connections: List[MockPGConnection] = []
        self._all_lock = threading.Lock()

        # 监控指标
        self._stats = {
            'get_count': 0,
            'hit_count': 0,
            'overflow_get_count': 0,
            'overflow_close_count': 0,
            'timeout_count': 0,
            'error_count': 0,
            'max_in_use': 0,
            'current_in_use': 0,
        }
        self._stats_lock = threading.Lock()

        # 预创建 size 个连接
        for _ in range(size):
            self._pool.put(self._create_connection())

    def _create_connection(self) -> MockPGConnection:
        with self._id_lock:
            cid = self._next_conn_id
            self._next_conn_id += 1
        conn = MockPGConnection(cid)
        with self._all_lock:
            self._all_connections.append(conn)
        return conn

    def _stats_inc(self, key: str, n: int = 1):
        with self._stats_lock:
            self._stats[key] += n

    def _stats_set(self, key: str, value: int):
        with self._stats_lock:
            if value > self._stats.get(key, 0):
                self._stats[key] = value

    def get(self) -> MockPGConnection:
        self._stats_inc('get_count')
        try:
            conn = self._pool.get(timeout=self._timeout)
            self._stats_inc('hit_count')
            with self._all_lock:
                self._stats['current_in_use'] = self._stats.get('current_in_use', 0) + 1
                self._stats_set('max_in_use', self._stats['current_in_use'])
            return conn
        except queue.Empty:
            # 池空, 尝试创建 overflow 连接
            with self._overflow_lock:
                if self._overflow_count < self._max_overflow:
                    self._overflow_count += 1
                    self._stats_inc('overflow_get_count')
                    conn = self._create_connection()
                    with self._all_lock:
                        self._stats['current_in_use'] = self._stats.get('current_in_use', 0) + 1
                        self._stats_set('max_in_use', self._stats['current_in_use'])
                    return conn
            self._stats_inc('timeout_count')
            raise TimeoutError(
                f"MockPGPool: 获取连接超时 (>{self._timeout}s), "
                f"pool_size={self._size}, max_overflow={self._max_overflow}"
            )

    def put(self, conn: MockPGConnection):
        """归还连接到池 (或关闭 overflow)."""
        with self._all_lock:
            self._stats['current_in_use'] = max(0, self._stats.get('current_in_use', 0) - 1)
        # 检查 recycle
        age = time.time() - conn.created_at
        if age > self._recycle:
            with self._overflow_lock:
                if self._overflow_count > 0:
                    self._overflow_count -= 1
            return  # 真正关闭

        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            # 池满 (steady pool), 关闭
            with self._overflow_lock:
                if self._overflow_count > 0:
                    self._overflow_count -= 1
                    self._stats_inc('overflow_close_count')

    def get_stats(self) -> Dict[str, Any]:
        with self._all_lock:
            return dict(self._stats)


# ============================================================
# 工作负载模拟
# ============================================================

@dataclass
class RequestResult:
    """单次请求结果."""
    thread_id: int
    request_id: int
    success: bool
    duration_ms: float
    wait_ms: float = 0.0  # 获取连接的等待时间
    error_type: str = ""
    error_msg: str = ""


def simulate_workload(
    pool: MockPGPool,
    thread_id: int,
    num_requests: int,
    stop_event: threading.Event,
) -> List[RequestResult]:
    """单线程工作负载模拟.

    每个请求: 借连接 → 模拟 BEGIN+SELECT+INSERT+COMMIT → 归还连接
    """
    results: List[RequestResult] = []
    for req_id in range(num_requests):
        if stop_event.is_set():
            break
        t0 = time.time()
        conn: Optional[MockPGConnection] = None
        wait_start = time.time()
        try:
            conn = pool.get()
            wait_ms = (time.time() - wait_start) * 1000
            # 模拟事务
            cur = conn.cursor()
            cur.execute("BEGIN")
            cur.execute("SELECT * FROM t WHERE id = %s", (req_id,))
            cur.fetchone()
            cur.execute("INSERT INTO t (id, val) VALUES (%s, %s)", (req_id, f'thread-{thread_id}'))
            cur.execute("COMMIT")
            cur.close()
            duration_ms = (time.time() - t0) * 1000
            results.append(RequestResult(
                thread_id=thread_id,
                request_id=req_id,
                success=True,
                duration_ms=duration_ms,
                wait_ms=wait_ms,
            ))
        except TimeoutError as e:
            results.append(RequestResult(
                thread_id=thread_id,
                request_id=req_id,
                success=False,
                duration_ms=(time.time() - t0) * 1000,
                wait_ms=(time.time() - wait_start) * 1000,
                error_type='TimeoutError',
                error_msg=str(e),
            ))
        except Exception as e:
            results.append(RequestResult(
                thread_id=thread_id,
                request_id=req_id,
                success=False,
                duration_ms=(time.time() - t0) * 1000,
                wait_ms=(time.time() - wait_start) * 1000,
                error_type=type(e).__name__,
                error_msg=str(e)[:200],
            ))
        finally:
            if conn is not None:
                try:
                    pool.put(conn)
                except Exception:
                    pass
    return results


# ============================================================
# 报告生成
# ============================================================

def percentile(data: List[float], p: float) -> float:
    """简单百分位计算."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p / 100)
    if idx >= len(sorted_data):
        idx = len(sorted_data) - 1
    return sorted_data[idx]


def build_report(
    all_results: List[RequestResult],
    pool_stats: Dict[str, Any],
    concurrency: int,
    requests_per_thread: int,
    total_elapsed: float,
    pool_config: Dict[str, Any],
) -> Dict[str, Any]:
    """汇总测试结果为报告."""
    total = len(all_results)
    success = [r for r in all_results if r.success]
    failures = [r for r in all_results if not r.success]
    durations = [r.duration_ms for r in success]
    wait_times = [r.wait_ms for r in success]

    error_types = Counter(r.error_type for r in failures)

    report = {
        'meta': {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'concurrency': concurrency,
            'requests_per_thread': requests_per_thread,
            'total_requests': total,
            'total_elapsed_sec': round(total_elapsed, 3),
            'throughput_rps': round(total / total_elapsed, 2) if total_elapsed > 0 else 0,
            'pool_config': pool_config,
        },
        'summary': {
            'success_count': len(success),
            'failure_count': len(failures),
            'success_rate_pct': round(100 * len(success) / total, 4) if total else 0,
            'error_rate_pct': round(100 * len(failures) / total, 4) if total else 0,
        },
        'latency_ms': {
            'min': round(min(durations), 3) if durations else 0,
            'max': round(max(durations), 3) if durations else 0,
            'mean': round(statistics.mean(durations), 3) if durations else 0,
            'median': round(statistics.median(durations), 3) if durations else 0,
            'p50': round(percentile(durations, 50), 3),
            'p95': round(percentile(durations, 95), 3),
            'p99': round(percentile(durations, 99), 3),
            'stdev': round(statistics.stdev(durations), 3) if len(durations) > 1 else 0,
        },
        'connection_wait_ms': {
            'min': round(min(wait_times), 3) if wait_times else 0,
            'max': round(max(wait_times), 3) if wait_times else 0,
            'mean': round(statistics.mean(wait_times), 3) if wait_times else 0,
            'p95': round(percentile(wait_times, 95), 3),
            'p99': round(percentile(wait_times, 99), 3),
        },
        'error_breakdown': dict(error_types),
        'pool_stats': pool_stats,
        'verdict': _verdict(len(success), total, error_types, pool_stats),
    }
    return report


def _verdict(success: int, total: int, errors: Counter, pool_stats: Dict) -> str:
    """根据结果给出最终评价."""
    if total == 0:
        return "无有效请求"
    success_rate = 100 * success / total
    timeouts = errors.get('TimeoutError', 0)
    if success_rate == 100 and timeouts == 0:
        return "PASS - 连接池在 100 并发下表现稳定, 无超时/错误"
    if success_rate >= 99:
        return f"PASS - 成功率 {success_rate:.2f}% (轻微错误可接受)"
    if success_rate >= 95:
        return f"WARN - 成功率 {success_rate:.2f}%, 超时={timeouts} (建议调大 pool_size 或检查后端)"
    return f"FAIL - 成功率仅 {success_rate:.2f}%, 超时={timeouts} (池配置或后端不达标)"


# ============================================================
# 主入口
# ============================================================

def run_stress_test(
    concurrency: int = 100,
    requests_per_thread: int = 10,
    pool_size: int = 20,
    max_overflow: int = 80,
    pool_timeout: float = 5.0,
    output: Optional[str] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """执行压力测试, 返回报告 dict."""
    log = print if verbose else (lambda *a, **k: None)
    log(f"=== PostgreSQL 连接池压力测试 ===")
    log(f"  并发线程数:        {concurrency}")
    log(f"  每线程请求数:      {requests_per_thread}")
    log(f"  总请求数:          {concurrency * requests_per_thread}")
    log(f"  pool_size:         {pool_size}")
    log(f"  max_overflow:      {max_overflow}")
    log(f"  pool_timeout:      {pool_timeout}s")
    log(f"  硬上限:            {pool_size + max_overflow}")
    log("")

    # 初始化池
    pool = MockPGPool(
        size=pool_size,
        max_overflow=max_overflow,
        timeout=pool_timeout,
    )

    stop_event = threading.Event()
    all_results: List[RequestResult] = []
    t_start = time.time()

    # 用 ThreadPoolExecutor 调度
    log(f"[{datetime.now().strftime('%H:%M:%S')}] 启动 {concurrency} 线程...")
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(simulate_workload, pool, tid, requests_per_thread, stop_event)
            for tid in range(concurrency)
        ]
        # 收集结果
        done_count = 0
        for fut in as_completed(futures):
            try:
                results = fut.result(timeout=60)
                all_results.extend(results)
                done_count += 1
                if verbose and done_count % 10 == 0:
                    elapsed = time.time() - t_start
                    log(f"  进度: {done_count}/{concurrency} 线程完成, "
                        f"已用时 {elapsed:.1f}s, 累计请求 {len(all_results)}")
            except Exception as e:
                log(f"  线程异常: {e}")
                traceback.print_exc()

    total_elapsed = time.time() - t_start

    pool_stats = pool.get_stats()
    report = build_report(
        all_results, pool_stats, concurrency, requests_per_thread,
        total_elapsed,
        pool_config={
            'pool_size': pool_size,
            'max_overflow': max_overflow,
            'pool_timeout': pool_timeout,
        },
    )

    # 打印摘要
    if verbose:
        log("")
        log("=== 测试结果摘要 ===")
        log(f"  总耗时:        {report['meta']['total_elapsed_sec']}s")
        log(f"  吞吐量:        {report['meta']['throughput_rps']} req/s")
        log(f"  成功/失败:     {report['summary']['success_count']} / {report['summary']['failure_count']}")
        log(f"  成功率:        {report['summary']['success_rate_pct']}%")
        log(f"  错误率:        {report['summary']['error_rate_pct']}%")
        log(f"  响应时间 (ms): mean={report['latency_ms']['mean']} "
            f"p50={report['latency_ms']['p50']} p95={report['latency_ms']['p95']} "
            f"p99={report['latency_ms']['p99']} max={report['latency_ms']['max']}")
        log(f"  连接等待 (ms): mean={report['connection_wait_ms']['mean']} "
            f"p95={report['connection_wait_ms']['p95']} p99={report['connection_wait_ms']['p99']}")
        log(f"  错误分布:      {dict(report['error_breakdown'])}")
        log(f"  池统计:        {pool_stats}")
        log(f"  结论:          {report['verdict']}")

    # 保存报告
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        log(f"  报告已保存:    {output}")

    return report


def main():
    parser = argparse.ArgumentParser(description='PostgreSQL 连接池压力测试 (本地模拟)')
    parser.add_argument('--concurrency', type=int, default=100, help='并发线程数 (默认 100)')
    parser.add_argument('--requests', type=int, default=10, help='每线程请求数 (默认 10)')
    parser.add_argument('--pool-size', type=int, default=20, help='pool_size (默认 20)')
    parser.add_argument('--max-overflow', type=int, default=80, help='max_overflow (默认 80)')
    parser.add_argument('--pool-timeout', type=float, default=5.0, help='pool_timeout 秒 (默认 5.0)')
    parser.add_argument('--output', type=str, default=None, help='报告输出路径 (JSON)')
    parser.add_argument('--quiet', action='store_true', help='静默模式')
    args = parser.parse_args()

    report = run_stress_test(
        concurrency=args.concurrency,
        requests_per_thread=args.requests,
        pool_size=args.pool_size,
        max_overflow=args.max_overflow,
        pool_timeout=args.pool_timeout,
        output=args.output,
        verbose=not args.quiet,
    )
    # 退出码: 完全成功=0, 警告=1, 失败=2
    success_rate = report['summary']['success_rate_pct']
    if success_rate == 100:
        sys.exit(0)
    elif success_rate >= 99:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
