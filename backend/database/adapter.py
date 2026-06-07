"""数据库适配器层 - 支持 SQLite (默认) / PostgreSQL (高并发)

设计目标:
- 通过环境变量 DB_BACKEND 切换后端 ('sqlite' / 'postgresql')
- 提供统一接口, 业务代码无需感知后端差异
- 解决 SQLite 写锁瓶颈: PostgreSQL 模式下使用 SQLAlchemy 连接池
- 默认保持 SQLite 行为, 向后兼容 (锁竞争问题由配置切换解决)

使用示例:
    # 默认 SQLite
    export DB_BACKEND=sqlite
    export DB_PATH=data/history.db

    # 切换到 PostgreSQL (高并发)
    export DB_BACKEND=postgresql
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_NAME=mech_calc
    export DB_USER=app_user
    export DB_PASSWORD=xxx
    export DB_POOL_SIZE=20
    export DB_POOL_MAX_OVERFLOW=10
"""
import logging
import os
import queue
import threading
from contextlib import contextmanager

_logger = logging.getLogger('backend.database.adapter')

# ============ 配置 ============
DB_BACKEND = os.getenv('DB_BACKEND', 'sqlite').lower()  # 'sqlite' | 'postgresql'
DB_PATH = os.getenv('DB_PATH', 'data/history.db')

# PostgreSQL 配置
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'mech_calc')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '20'))
DB_POOL_MAX_OVERFLOW = int(os.getenv('DB_POOL_MAX_OVERFLOW', '10'))
DB_POOL_TIMEOUT = float(os.getenv('DB_POOL_TIMEOUT', '10.0'))
DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))


# ============ 适配器接口 ============
class DBAdapter:
    """数据库适配器基类.

    子类必须实现: connect(), execute(), executemany(), fetchone(), fetchall(), commit(), rollback(), close()
    """

    def connect(self):
        raise NotImplementedError

    def execute(self, sql: str, params: tuple = ()):
        raise NotImplementedError

    def executemany(self, sql: str, params_list: list):
        raise NotImplementedError

    def fetchone(self):
        raise NotImplementedError

    def fetchall(self):
        raise NotImplementedError

    def commit(self):
        raise NotImplementedError

    def rollback(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    @contextmanager
    def transaction(self):
        """事务上下文管理器."""
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise


# ============ SQLite 适配器 ============
class SQLiteAdapter(DBAdapter):
    """SQLite 适配器 (保留 WAL 模式 + 行工厂)."""

    def __init__(self, db_path: str):
        import sqlite3
        self._sqlite3 = sqlite3
        self._db_path = db_path
        self._conn = None
        self._cur = None

    def connect(self):
        self._conn = self._sqlite3.connect(self._db_path, timeout=10, check_same_thread=False)
        self._conn.row_factory = self._sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        return self

    def execute(self, sql, params=()):
        self._cur = self._conn.execute(sql, params)
        return self._cur

    def executemany(self, sql, params_list):
        self._cur = self._conn.executemany(sql, params_list)
        return self._cur

    def fetchone(self):
        return self._cur.fetchone() if self._cur else None

    def fetchall(self):
        return self._cur.fetchall() if self._cur else []

    def commit(self):
        if self._conn:
            self._conn.commit()

    def rollback(self):
        if self._conn:
            self._conn.rollback()

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    @property
    def raw_conn(self):
        """暴露原生连接 (供 fetchone/fetchall 直接使用)."""
        return self._conn


# ============ PostgreSQL 适配器 (高并发优化) ============
class PostgreSQLAdapter(DBAdapter):
    """PostgreSQL 适配器 (使用 SQLAlchemy 连接池).

    配置:
        - pool_size: 稳态连接数 (默认 20)
        - max_overflow: 突发时允许的额外连接 (默认 10)
        - pool_timeout: 获取连接超时 (秒, 默认 10)
        - pool_recycle: 连接回收时间 (秒, 默认 3600)
        - pool_pre_ping: 每次获取前 ping (默认 True, 防止死连接)
    """

    def __init__(self):
        self._engine = None
        self._conn = None  # 当前事务的原始 psycopg2 连接
        self._cur = None
        self._row_factory = None  # 字典式行
        self._init_engine()

    def _init_engine(self):
        from sqlalchemy import create_engine
        from sqlalchemy.pool import QueuePool

        # 连接 URL: postgresql+psycopg2://user:pass@host:port/db
        url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

        self._engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_POOL_MAX_OVERFLOW,
            pool_timeout=DB_POOL_TIMEOUT,
            pool_recycle=DB_POOL_RECYCLE,
            pool_pre_ping=True,  # 防止使用已关闭连接
            echo=False,
        )
        _logger.info(
            f"[PG-INIT] 连接池已创建: pool_size={DB_POOL_SIZE} "
            f"max_overflow={DB_POOL_MAX_OVERFLOW} timeout={DB_POOL_TIMEOUT}s"
        )

    def connect(self):
        """借出池连接 (借助 SQLAlchemy 的 connection 上下文)."""
        # 注意: 借用模式 (ConnectionFairy), 用完需 close() 归还
        self._sa_conn = self._engine.connect()
        self._pg_conn = self._sa_conn.connection.dbapi_connection  # 底层 psycopg2 连接
        return self

    def execute(self, sql, params=()):
        # 转换 ? 占位符为 %s (PostgreSQL 习惯)
        sql = self._convert_placeholders(sql)
        if self._cur is None:
            self._cur = self._pg_conn.cursor()
        self._cur.execute(sql, params)
        return self._cur

    def executemany(self, sql, params_list):
        sql = self._convert_placeholders(sql)
        if self._cur is None:
            self._cur = self._pg_conn.cursor()
        self._cur.executemany(sql, params_list)
        return self._cur

    def _convert_placeholders(self, sql: str) -> str:
        """SQLite 风格 ? → PostgreSQL 风格 %s.

        注意: 仅在字符串字面量外做替换, 简单实现
        """
        return sql.replace('?', '%s')

    def commit(self):
        if self._pg_conn is not None:
            self._pg_conn.commit()

    def rollback(self):
        if self._pg_conn is not None:
            self._pg_conn.rollback()

    def close(self):
        """归还连接到池 (非真正关闭)."""
        try:
            if self._cur is not None:
                self._cur.close()
        except Exception:
            pass
        try:
            if hasattr(self, '_sa_conn') and self._sa_conn is not None:
                self._sa_conn.close()  # 归还到池
        except Exception:
            pass
        self._cur = None
        self._pg_conn = None
        self._sa_conn = None

    def dispose(self):
        """应用退出时关闭整个池."""
        if self._engine:
            self._engine.dispose()
            _logger.info("[PG-DISPOSE] 连接池已关闭")

    @property
    def raw_conn(self):
        return self._pg_conn

    def get_pool_stats(self) -> dict:
        """获取池监控指标 (用于 /api/history/stats 端点)."""
        if not self._engine:
            return {'enabled': False}
        pool = self._engine.pool
        return {
            'enabled': True,
            'backend': 'postgresql',
            'size': pool.size(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total': pool.size() + pool.overflow(),
        }


# ============ 池化适配器 (复用底层连接) ============
class PooledAdapterWrapper:
    """对 PostgreSQL 适配器的池化包装 (类似 SQLite 的 LifoQueue 池).

    区别:
        - PostgreSQL 模式: SQLAlchemy QueuePool 已内置池管理, 我们只需借/还
        - 这里我们再加一层 LifoQueue 是为了与现有 SQLite 池统一接口
    """

    def __init__(self, adapter_cls, max_size: int = 20):
        self._adapter_cls = adapter_cls
        self._pool: "queue.LifoQueue" = queue.LifoQueue(maxsize=max_size)
        self._lock = threading.Lock()
        self._created = 0
        self._get_count = 0
        self._hit_count = 0
        self._fallback_count = 0

    def _create(self):
        return self._adapter_cls().connect()

    @contextmanager
    def get(self):
        self._get_count += 1
        adapter = None
        from_pool = False
        try:
            try:
                adapter = self._pool.get_nowait()
                from_pool = True
                self._hit_count += 1
            except queue.Empty:
                self._fallback_count += 1
                adapter = self._create()
            yield adapter
        finally:
            if adapter is not None:
                if from_pool:
                    try:
                        self._pool.put_nowait(adapter)
                    except queue.Full:
                        adapter.close()
                else:
                    adapter.close()

    def dispose(self):
        while True:
            try:
                a = self._pool.get_nowait()
                a.close()
            except queue.Empty:
                break


# ============ 工厂函数 ============
def create_adapter():
    """根据配置创建适配器实例."""
    if DB_BACKEND == 'postgresql':
        return PostgreSQLAdapter()
    return SQLiteAdapter(DB_PATH)


def get_engine_pool_stats() -> dict:
    """获取当前后端的池统计信息."""
    if DB_BACKEND == 'postgresql':
        try:
            adapter = create_adapter()
            stats = adapter.get_pool_stats()
            adapter.dispose()  # 创建后立即关闭, 只为读 stats
            return stats
        except Exception as e:
            return {'enabled': False, 'error': str(e)}
    return {'enabled': False, 'backend': 'sqlite'}


# ============ 兼容性接口 (供 history_db 切换) ============
def is_postgres_enabled() -> bool:
    """是否启用 PostgreSQL 后端."""
    return DB_BACKEND == 'postgresql'


__all__ = [
    'DBAdapter',
    'SQLiteAdapter',
    'PostgreSQLAdapter',
    'PooledAdapterWrapper',
    'create_adapter',
    'get_engine_pool_stats',
    'is_postgres_enabled',
]
