"""单元测试: backend/database/history_db.py 连接池 (方案 B)

覆盖范围:
  - init_pool: 池大小、预创建、幂等性
  - get_pooled_connection: LIFO 策略、健康检查、降级
  - 监控指标: hit_count / fallback_count / health_fail_count
  - close_pool: 优雅关闭
  - 与 _connect 集成: 通过环境变量自动启用
  - 错误处理: 池空超时、连接损坏
"""
import os
import queue
import sqlite3
import time
import threading
from pathlib import Path

import pytest

import backend.database.history_db as hdb


@pytest.fixture(autouse=True)
def reset_pool():
    """每个测试前重置连接池状态."""
    hdb._pool_initialized = False
    # 清空池
    while not hdb._pool.empty():
        try:
            conn = hdb._pool.get_nowait()
            conn.close()
        except Exception:
            pass
    hdb._pool_created_count = 0
    hdb._pool_get_count = 0
    hdb._pool_hit_count = 0
    hdb._pool_fallback_count = 0
    hdb._pool_health_fail_count = 0
    # 重置 DB 路径
    hdb._db_path = None
    hdb._initialized = False
    yield


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """临时数据库 fixture.

    关键: 在 init_db() 之前禁用 ENABLE_CONN_POOL, 避免 init_db 自动初始化池
    (size=POOL_SIZE=8, 来自环境变量), 影响 init_pool(size=N) 测试的断言.
    各测试用例可按需重新启用并调用 init_pool.
    """
    db_path = tmp_path / 'pool_test.db'
    # 禁用 init_db() 内部的自动池初始化
    monkeypatch.setattr(hdb, 'ENABLE_CONN_POOL', False)
    hdb.init_db(db_path)
    return db_path


class TestInitPool:
    """init_pool 函数测试."""

    def test_init_pool_creates_connections(self, temp_db):
        """init_pool 应预创建全部连接."""
        hdb.init_pool(size=3)
        assert hdb._pool_initialized is True
        assert hdb._pool.qsize() == 3
        assert hdb._pool_created_count == 3

    def test_init_pool_default_size(self, temp_db):
        """默认池大小应能通过 init_pool(size=N) 自定义."""
        # 显式指定 size=7, 不依赖 POOL_SIZE 常量
        hdb.init_pool(size=7)
        # 池中应有 7 个连接 (init_pool 内部按 size 创建)
        assert hdb._pool.qsize() == 7
        assert hdb._pool_created_count == 7

    def test_init_pool_idempotent(self, temp_db):
        """多次 init_pool 应是幂等的 (只初始化一次)."""
        hdb.init_pool(size=2)
        size_after_first = hdb._pool.qsize()
        hdb.init_pool(size=5)  # 第二次调用
        # 池大小应保持第一次的值 (不重复初始化)
        assert hdb._pool.qsize() == size_after_first
        assert hdb._pool_created_count == size_after_first

    def test_init_pool_without_db_raises(self):
        """未初始化 DB 时 init_pool 应抛 RuntimeError."""
        with pytest.raises(RuntimeError, match="数据库未初始化"):
            hdb.init_pool(size=2)

    def test_init_pool_logs_init_event(self, temp_db, caplog):
        """init_pool 应记录 POOL-INIT 日志."""
        import logging
        with caplog.at_level(logging.INFO, logger='backend.database.history_db'):
            hdb.init_pool(size=2)
        assert any('[POOL-INIT]' in rec.message for rec in caplog.records)


class TestGetPooledConnection:
    """get_pooled_connection 上下文管理器测试."""

    def test_get_returns_connection(self, temp_db):
        """get_pooled_connection 应返回可用连接."""
        hdb.init_pool(size=2)
        with hdb.get_pooled_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)
            cur = conn.execute("SELECT 1 AS v")
            assert cur.fetchone()['v'] == 1

    def test_get_increments_counters(self, temp_db):
        """每次获取应递增计数器."""
        hdb.init_pool(size=2)
        with hdb.get_pooled_connection():
            pass
        with hdb.get_pooled_connection():
            pass
        assert hdb._pool_get_count == 2
        assert hdb._pool_hit_count == 2
        assert hdb._pool_fallback_count == 0

    def test_pool_empty_falls_back(self, temp_db):
        """池空时应降级到新建连接."""
        hdb.init_pool(size=1)
        # 模拟占用唯一一个连接
        conn_busy = hdb._pool.get()

        try:
            with hdb.get_pooled_connection() as conn2:
                # 这个连接应该是新建的, 不是池中的
                assert conn2 is not conn_busy
        finally:
            # 归还 busy 连接
            hdb._pool.put(conn_busy)

        assert hdb._pool_fallback_count >= 1

    def test_lifo_strategy(self, temp_db):
        """LIFO 策略: 后进先出, 验证连接复用."""
        hdb.init_pool(size=2)
        with hdb.get_pooled_connection() as conn1:
            pass
        with hdb.get_pooled_connection() as conn2:
            # LIFO: 第二次 get 应返回刚放回的 conn1
            assert conn2 is conn1

    def test_commit_on_normal_exit(self, temp_db):
        """上下文正常退出时应提交事务."""
        hdb.init_pool(size=1)
        hdb.clear_all()
        with hdb.get_pooled_connection() as conn:
            conn.execute(
                "INSERT INTO calc_history (ts, category, endpoint, input_json, output_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (time.time(), 'test', '/test', '{}', '{}')
            )
        # 提交后应能查到
        assert hdb.count_records() == 1

    def test_rollback_on_exception(self, temp_db):
        """上下文异常退出时应回滚事务."""
        hdb.init_pool(size=1)
        hdb.clear_all()
        with pytest.raises(RuntimeError):
            with hdb.get_pooled_connection() as conn:
                conn.execute(
                    "INSERT INTO calc_history (ts, category, endpoint, input_json, output_json) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (time.time(), 'test', '/test', '{}', '{}')
                )
                raise RuntimeError("测试异常")
        # 回滚后应为 0
        assert hdb.count_records() == 0

    def test_connection_returned_to_pool(self, temp_db):
        """上下文退出后, 连接应被放回池中."""
        hdb.init_pool(size=2)
        initial_qsize = hdb._pool.qsize()
        with hdb.get_pooled_connection():
            pass
        assert hdb._pool.qsize() == initial_qsize


class TestHealthCheck:
    """健康检查测试."""

    def test_health_check_passing_connection(self, temp_db):
        """健康连接应通过 SELECT 1."""
        hdb.init_pool(size=1)
        conn = hdb._create_pooled_connection()
        try:
            assert hdb._health_check(conn) is True
        finally:
            conn.close()

    def test_health_check_closed_connection(self, temp_db):
        """关闭的连接应失败."""
        hdb.init_pool(size=1)
        conn = hdb._create_pooled_connection()
        conn.close()
        assert hdb._health_check(conn) is False

    def test_unhealthy_connection_replaced(self, temp_db):
        """不健康的连接应被替换."""
        hdb.init_pool(size=1)
        # 取出连接, 手动关闭 (模拟损坏)
        conn = hdb._pool.get()
        conn.close()
        hdb._pool.put(conn)  # 放回损坏的连接

        # 获取时, 健康检查失败, 应创建新连接
        with hdb.get_pooled_connection() as new_conn:
            assert new_conn is not conn  # 不是损坏的那个
        # 健康检查失败计数应增加
        assert hdb._pool_health_fail_count >= 1


class TestPoolStats:
    """监控指标测试."""

    def test_get_pool_stats_initial(self, temp_db):
        """未初始化池时的统计."""
        stats = hdb.get_pool_stats()
        assert stats['enabled'] is False
        assert stats['qsize'] == 0
        assert stats['created'] == 0

    def test_get_pool_stats_after_usage(self, temp_db):
        """使用后的统计指标."""
        hdb.init_pool(size=3)
        # 模拟 10 次获取, 8 次命中
        for _ in range(8):
            with hdb.get_pooled_connection():
                pass
        # 2 次降级 (超出池大小)
        # 先占用所有连接
        busy = [hdb._pool.get() for _ in range(3)]
        for _ in range(2):
            with hdb.get_pooled_connection():
                pass
        for c in busy:
            hdb._pool.put(c)

        stats = hdb.get_pool_stats()
        assert stats['enabled'] is True
        assert stats['size'] == 3
        assert stats['get_count'] == 10
        assert stats['hit_count'] == 8
        assert stats['fallback_count'] == 2
        assert stats['hit_rate'] == 80.0
        assert stats['fallback_rate'] == 20.0


class TestClosePool:
    """close_pool 测试."""

    def test_close_pool_closes_all(self, temp_db):
        """close_pool 应关闭所有池中连接."""
        hdb.init_pool(size=3)
        assert hdb._pool.qsize() == 3
        hdb.close_pool()
        assert hdb._pool_initialized is False
        # 池应清空
        assert hdb._pool.qsize() == 0

    def test_close_pool_idempotent(self, temp_db):
        """多次 close_pool 不会出错."""
        hdb.init_pool(size=2)
        hdb.close_pool()
        hdb.close_pool()  # 第二次调用不报错
        assert hdb._pool_initialized is False


class TestIntegrationWithConnect:
    """与 _connect() 的集成测试."""

    def test_connect_uses_pool_when_enabled(self, temp_db, monkeypatch):
        """ENABLE_CONN_POOL=1 时 _connect 应使用池."""
        monkeypatch.setattr(hdb, 'ENABLE_CONN_POOL', True)
        hdb.init_pool(size=2)

        with hdb._connect() as conn:
            cur = conn.execute("SELECT 1 AS v")
            assert cur.fetchone()['v'] == 1
        # 应计入池统计
        assert hdb._pool_get_count == 1

    def test_connect_uses_short_when_disabled(self, temp_db, monkeypatch):
        """默认 _connect 应使用短连接模式."""
        monkeypatch.setattr(hdb, 'ENABLE_CONN_POOL', False)
        # 池未启用, _connect 应使用短连接
        with hdb._connect() as conn:
            cur = conn.execute("SELECT 1 AS v")
            assert cur.fetchone()['v'] == 1
        # 池统计应无变化
        assert hdb._pool_get_count == 0

    def test_init_db_auto_inits_pool(self, temp_db, monkeypatch):
        """当 ENABLE_CONN_POOL=1 时, init_db 应自动初始化池."""
        monkeypatch.setattr(hdb, 'ENABLE_CONN_POOL', True)
        # 重新调用 init_db 触发自动池初始化
        hdb.init_db(temp_db)
        assert hdb._pool_initialized is True
        assert hdb._pool.qsize() == hdb.POOL_SIZE

    def test_init_db_path_change_closes_old_pool(self, tmp_path, monkeypatch):
        """回归测试: 重新初始化不同路径时必须关闭旧池.

        Bug 场景:
          1. 测试 A 用 tmp_path/a.db 初始化, 触发池自动创建
          2. tmp_path/a.db 被 pytest 清理
          3. 测试 B 用 tmp_path/b.db 初始化
          4. 若不关闭旧池, 池中连接仍指向 a.db (已被删)
          5. 执行 schema 时, 写入 a.db 不存在, 而 b.db 未被创建 -> b.db 缺失
        """
        monkeypatch.setattr(hdb, 'ENABLE_CONN_POOL', True)

        # 1. 第一个 DB 路径
        path_a = tmp_path / 'a.db'
        hdb.init_db(path_a)
        assert hdb._pool_initialized is True
        assert hdb._pool.qsize() == hdb.POOL_SIZE

        # 2. 模拟旧 DB 被清理 (此处仅模拟路径变化, 不真正删除)
        # 3. 第二个 DB 路径
        path_b = tmp_path / 'b.db'
        hdb.init_db(path_b)

        # 4. 验证: 新 DB 文件应存在 (说明 schema 写入了正确位置)
        assert path_b.exists(), f"新 DB {path_b} 未创建, 池中旧连接干扰了初始化"
        # 5. 验证: 池中连接应指向新 DB
        with hdb._connect() as conn:
            cur = conn.execute("SELECT 1 AS v")
            assert cur.fetchone()['v'] == 1

    def test_init_db_same_path_no_pool_reinit(self, temp_db, monkeypatch):
        """同一路径重复 init_db 不应重建池 (幂等性)."""
        monkeypatch.setattr(hdb, 'ENABLE_CONN_POOL', True)
        hdb.init_db(temp_db)  # 自动初始化池
        created_count_before = hdb._pool_created_count

        hdb.init_db(temp_db)  # 同一路径, 不应重建
        # created_count 不变 (池未重建)
        assert hdb._pool_created_count == created_count_before
        assert hdb._pool_initialized is True


class TestConcurrentAccess:
    """并发场景测试 (模拟真实压测)."""

    def test_concurrent_writes_no_data_loss(self, temp_db, monkeypatch):
        """并发写入不应丢失数据."""
        # 启用连接池模式 (否则 _connect 走短连接)
        monkeypatch.setattr(hdb, 'ENABLE_CONN_POOL', True)
        hdb.init_pool(size=5)
        hdb.clear_all()

        n_threads = 3
        n_per_thread = 2
        barrier = threading.Barrier(n_threads)
        results = []
        results_lock = threading.Lock()

        def worker(uid):
            barrier.wait()  # 同步起跑
            for i in range(n_per_thread):
                rec_id = hdb.add_record(
                    category='pool_concurrent',
                    endpoint=f'/pool/test/{uid}/{i}',
                    input_data={'uid': uid, 'i': i},
                    output_data={'result': uid * 100 + i},
                )
                with results_lock:
                    results.append(rec_id)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # 验证数据完整性
        assert len(results) == n_threads * n_per_thread
        assert hdb.count_records(category='pool_concurrent') == n_threads * n_per_thread
        # 池统计应非空
        stats = hdb.get_pool_stats()
        assert stats['get_count'] > 0
        # 至少有一些成功 (命中 + 降级)
        assert stats['hit_count'] + stats['fallback_count'] == stats['get_count']
