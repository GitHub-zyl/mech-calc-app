"""计算历史 SQLite 持久化模块

设计要点:
- 单例 DB 路径, 通过 init_db() 初始化表结构
- 使用 WAL 模式提升并发读
- 所有写操作使用事务
- 输入/输出以 JSON 字符串存储, 灵活支持嵌套结构
- 提供 list / get / add / delete / count / clear / stats 全套 CRUD
- 所有数据写入操作均带有结构化日志 (写入前/写入后 + 耗时)

v2.3.0 起增加连接池 (方案 B: Connection Pool):
- 默认短连接 (向后兼容), 通过 ENABLE_CONN_POOL=1 启用
- 池大小可配 (默认 5), LIFO 策略 (提高缓存命中率)
- 归还连接时执行健康检查 (SELECT 1), 损坏连接自动重建
- 池空时降级到新建连接 (不阻塞业务)
- 启动时预创建全部连接, 应用退出时统一关闭

Schema:
    calc_history (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        ts              REAL NOT NULL,           -- Unix timestamp
        category        TEXT NOT NULL,           -- 大类: gear / bearing / ...
        endpoint        TEXT NOT NULL,           -- API 路径
        calc_id         TEXT,                    -- 前端注册表 ID
        input_json      TEXT NOT NULL,
        output_json     TEXT NOT NULL,
        client_ip       TEXT,                    -- 客户端 IP
        duration_ms     REAL                     -- 计算耗时
    )

索引:
    idx_calc_history_ts   - 按时间倒序
    idx_calc_history_cat  - 按分类
"""
import json
import logging
import os
import queue
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any, Iterable


# ============== 日志配置 ==============
# 模块级 logger, 可被 root logger 统一配置
_logger = logging.getLogger('backend.database.history_db')
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] [%(threadName)s(tid=%(thread)d)] %(message)s'
    ))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


def _truncate(s: str, n: int = 200) -> str:
    """截断长字符串, 避免日志爆炸."""
    if s is None:
        return 'None'
    s = str(s)
    return s if len(s) <= n else s[:n] + f'...<{len(s) - n} more>'


def _log_write_start(op: str, **fields) -> float:
    """记录写操作开始. 返回开始时间戳 (time.perf_counter)."""
    ts = time.time()
    fields_str = ' '.join(f'{k}={_truncate(v, 80)!r}' for k, v in fields.items() if v is not None)
    _logger.info(
        f"[WRITE-START] op={op} ts={ts:.6f} {fields_str}"
    )
    return time.perf_counter()


def _log_write_end(op: str, start: float, **fields) -> None:
    """记录写操作结束 + 耗时."""
    elapsed_ms = (time.perf_counter() - start) * 1000
    fields_str = ' '.join(f'{k}={v!r}' for k, v in fields.items())
    _logger.info(
        f"[WRITE-END]   op={op} elapsed={elapsed_ms:.3f}ms {fields_str}"
    )


_SCHEMA = """
CREATE TABLE IF NOT EXISTS calc_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL,
    category    TEXT    NOT NULL,
    endpoint    TEXT    NOT NULL,
    calc_id     TEXT,
    input_json  TEXT    NOT NULL,
    output_json TEXT    NOT NULL,
    client_ip   TEXT,
    duration_ms REAL
);

CREATE INDEX IF NOT EXISTS idx_calc_history_ts  ON calc_history(ts DESC);
CREATE INDEX IF NOT EXISTS idx_calc_history_cat ON calc_history(category);
"""


# 模块级单例
_lock = threading.Lock()
_db_path: Optional[Path] = None
_initialized: bool = False


# ============== 连接池 (方案 B) ==============
# 通过环境变量控制, 保持向后兼容
ENABLE_CONN_POOL = os.getenv('ENABLE_CONN_POOL', '0') == '1'
POOL_SIZE = int(os.getenv('CONN_POOL_SIZE', '5'))  # 池大小
POOL_GET_TIMEOUT = float(os.getenv('CONN_POOL_TIMEOUT', '5.0'))  # 获取连接超时 (秒)

# LIFO 池 (LIFO 策略: 后进先出, 提高热点连接的缓存命中率)
_pool: "queue.LifoQueue[sqlite3.Connection]" = queue.LifoQueue(maxsize=POOL_SIZE)
_pool_lock = threading.Lock()
_pool_initialized: bool = False
_pool_created_count: int = 0  # 已创建的连接数
_pool_get_count: int = 0     # 获取连接次数
_pool_hit_count: int = 0     # 命中次数
_pool_fallback_count: int = 0  # 降级新建次数
_pool_health_fail_count: int = 0  # 健康检查失败次数


def _create_pooled_connection() -> sqlite3.Connection:
    """创建一个池化连接, 已配置 PRAGMA."""
    if _db_path is None:
        raise RuntimeError("数据库未初始化, 请先调用 init_db()")
    conn = sqlite3.connect(str(_db_path), timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # 复用 init_db 的 PRAGMA 设置
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _health_check(conn: sqlite3.Connection) -> bool:
    """验证连接是否可用. 失败则返回 False."""
    try:
        conn.execute("SELECT 1").fetchone()
        return True
    except (sqlite3.Error, Exception):
        return False


def init_pool(size: int = POOL_SIZE) -> None:
    """初始化连接池 (应用启动时调用一次).

    Args:
        size: 池大小 (默认 5, 来自 CONN_POOL_SIZE 环境变量)

    Raises:
        RuntimeError: 数据库未初始化
    """
    global _pool_initialized, _pool_created_count, POOL_SIZE, _pool
    if _db_path is None:
        raise RuntimeError("数据库未初始化, 请先调用 init_db()")

    with _pool_lock:
        # 幂等性: 已初始化则跳过, 保持原池大小
        if _pool_initialized:
            _logger.info(
                f"[POOL-SKIP] 连接池已初始化 (size={POOL_SIZE}), "
                f"忽略新 size={size}"
            )
            return

        # 调整池大小
        if size != POOL_SIZE:
            POOL_SIZE = size
            # 重建 pool 以支持新 maxsize (queue.LifoQueue 不支持动态调整 maxsize)
            _pool = queue.LifoQueue(maxsize=POOL_SIZE)

        start = time.perf_counter()
        # 预创建全部连接
        for i in range(POOL_SIZE):
            try:
                conn = _create_pooled_connection()
                _pool.put(conn)
                _pool_created_count += 1
            except Exception as e:
                _logger.warning(f"[POOL-FAIL] 创建连接 #{i} 失败: {e}")

        _pool_initialized = True
        elapsed_ms = (time.perf_counter() - start) * 1000
        _logger.info(
            f"[POOL-INIT] 连接池初始化完成: size={POOL_SIZE} "
            f"created={_pool_created_count} elapsed={elapsed_ms:.3f}ms"
        )


@contextmanager
def get_pooled_connection():
    """从池中获取连接 (上下文管理器).

    行为:
        1. 尝试从池中获取 (LIFO, 带超时)
        2. 健康检查 (SELECT 1)
        3. 失败时新建连接
        4. 归还时通过 _return_to_pool 放回池

    监控指标:
        - _pool_get_count: 总获取次数
        - _pool_hit_count: 命中池的次数
        - _pool_fallback_count: 降级到新建的次数
        - _pool_health_fail_count: 健康检查失败次数
    """
    global _pool_get_count, _pool_hit_count, _pool_fallback_count, _pool_health_fail_count
    _pool_get_count += 1

    conn = None
    from_pool = False
    try:
        if _pool_initialized:
            try:
                conn = _pool.get(timeout=POOL_GET_TIMEOUT)
                from_pool = True
                _pool_hit_count += 1
                # 健康检查
                if not _health_check(conn):
                    _pool_health_fail_count += 1
                    _logger.warning("[POOL-HEALTH] 健康检查失败, 创建新连接")
                    try:
                        conn.close()
                    except Exception:
                        pass
                    conn = _create_pooled_connection()
                    from_pool = False
                    _pool_fallback_count += 1
            except queue.Empty:
                # 池空 (超时), 降级到新建
                _pool_fallback_count += 1
                _logger.debug("[POOL-FALLBACK] 池空, 新建连接")
                conn = _create_pooled_connection()
        else:
            # 池未初始化, 降级到普通连接
            _pool_fallback_count += 1
            conn = _create_pooled_connection()

        yield conn
        # 业务代码无异常, 提交
        conn.commit()
    except Exception:
        # 业务代码异常, 回滚
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        # 归还连接
        if conn is not None:
            if _pool_initialized and from_pool and _health_check(conn):
                # 健康: 放回池
                try:
                    _pool.put_nowait(conn)
                except queue.Full:
                    # 池满 (理论上不会发生), 关闭
                    try:
                        conn.close()
                    except Exception:
                        pass
            else:
                # 不健康或非池连接: 关闭
                try:
                    conn.close()
                except Exception:
                    pass


def close_pool() -> None:
    """关闭连接池 (应用退出时调用)."""
    global _pool_initialized
    with _pool_lock:
        if not _pool_initialized:
            return
        closed = 0
        while True:
            try:
                conn = _pool.get_nowait()
                try:
                    conn.close()
                    closed += 1
                except Exception:
                    pass
            except queue.Empty:
                break
        _pool_initialized = False
        # 安全日志: 避免在 pytest / 解释器关闭时 stdout 已关闭引发 I/O 错误
        # logging 库内部会调用 handler.emit, stream 关闭时会 ValueError
        # 通过禁用错误传播 + 检查 stream 状态避免污染退出日志
        for handler in _logger.handlers[:]:
            stream = getattr(handler, 'stream', None)
            if stream is None or (hasattr(stream, 'closed') and stream.closed):
                _logger.removeHandler(handler)


def get_pool_stats() -> Dict[str, Any]:
    """获取连接池监控指标."""
    total = _pool_get_count or 1  # 避免除零
    return {
        'enabled': _pool_initialized,
        'size': POOL_SIZE,
        'qsize': _pool.qsize(),
        'created': _pool_created_count,
        'get_count': _pool_get_count,
        'hit_count': _pool_hit_count,
        'hit_rate': round(_pool_hit_count / total * 100, 2),
        'fallback_count': _pool_fallback_count,
        'fallback_rate': round(_pool_fallback_count / total * 100, 2),
        'health_fail_count': _pool_health_fail_count,
    }


def init_db(db_path: str | Path) -> Path:
    """初始化数据库. 多次调用是幂等的.

    关键: 重新初始化时 (db_path 变化), 必须先关闭旧池, 避免池中旧连接仍指向
    旧 DB 文件, 导致 schema 写入错误位置.
    """
    global _db_path, _initialized
    start = _log_write_start('init_db', db_path=str(db_path))
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        # 检测 DB 路径变化: 若已启用池且路径不同, 关闭旧池
        if ENABLE_CONN_POOL and _pool_initialized and _db_path is not None and _db_path != p:
            _logger.info(
                f"[POOL-CLOSE-BEFORE-INIT] DB 路径变化 ({_db_path} -> {p}), "
                f"关闭旧池"
            )
            close_pool()

        _db_path = p
        # 使用短连接执行 schema 初始化 (避免从池中拿到指向旧 DB 的连接)
        conn = sqlite3.connect(str(p), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            conn.executescript(_SCHEMA)
            # 启用 WAL 模式提升并发
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.commit()
        finally:
            conn.close()
        _initialized = True
    _log_write_end('init_db', start, path=str(p), initialized=True)

    # 方案 B: 如果启用了连接池, 自动初始化
    if ENABLE_CONN_POOL:
        init_pool(POOL_SIZE)

    return p


@contextmanager
def _connect():
    """获取连接.

    行为:
        - 启用池 (ENABLE_CONN_POOL=1): 使用 get_pooled_connection()
        - 默认 (短连接): 每次新建连接
    """
    if ENABLE_CONN_POOL and _pool_initialized:
        with get_pooled_connection() as conn:
            yield conn
        return

    # 短连接模式 (默认, 向后兼容)
    if _db_path is None:
        raise RuntimeError("数据库未初始化, 请先调用 init_db()")
    conn = sqlite3.connect(str(_db_path), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    # 反序列化 JSON
    for k in ('input_json', 'output_json'):
        if d.get(k):
            try:
                d[k.replace('_json', '')] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                d[k.replace('_json', '')] = d[k]
        else:
            d[k.replace('_json', '')] = None
    # 冗余字段 (兼容性)
    if d.get('input_json') and isinstance(d.get('input'), str):
        d['input'] = json.loads(d['input_json'])
    if d.get('output_json') and isinstance(d.get('output'), str):
        d['output'] = json.loads(d['output_json'])
    return d


# ============== CRUD ==============

def add_record(category: str, endpoint: str, input_data: Any, output_data: Any,
               calc_id: Optional[str] = None,
               client_ip: Optional[str] = None,
               duration_ms: Optional[float] = None,
               ts: Optional[float] = None) -> int:
    """插入一条历史记录, 返回新行 id."""
    if not category or not endpoint:
        raise ValueError("category 和 endpoint 必填")
    input_json = json.dumps(input_data, ensure_ascii=False)
    output_json = json.dumps(output_data, ensure_ascii=False)
    if ts is None:
        ts = time.time()

    # 写入前日志
    start = _log_write_start(
        'add_record',
        category=category,
        endpoint=endpoint,
        calc_id=calc_id,
        client_ip=client_ip,
        duration_ms=duration_ms,
        ts=ts,
        input_size=len(input_json),
        output_size=len(output_json),
        input_preview=_truncate(input_json, 120),
        output_preview=_truncate(output_json, 120),
    )

    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO calc_history
               (ts, category, endpoint, calc_id, input_json, output_json,
                client_ip, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ts, category, endpoint, calc_id, input_json, output_json,
             client_ip, duration_ms),
        )
        new_id = cur.lastrowid

    # 写入后日志
    _log_write_end('add_record', start, id=new_id, rowcount=cur.rowcount, status='ok')
    return new_id


def get_record(record_id: int) -> Optional[Dict[str, Any]]:
    """按 id 查询单条. 不存在返回 None."""
    start = time.perf_counter()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM calc_history WHERE id = ?", (record_id,)
        ).fetchone()
    elapsed = (time.perf_counter() - start) * 1000
    _logger.debug(f"[READ] op=get_record id={record_id} found={row is not None} elapsed={elapsed:.3f}ms")
    return _row_to_dict(row) if row else None


def list_records(limit: int = 20, offset: int = 0,
                 category: Optional[str] = None,
                 calc_id: Optional[str] = None,
                 since: Optional[float] = None,
                 until: Optional[float] = None) -> List[Dict[str, Any]]:
    """分页+筛选历史记录 (按时间倒序)."""
    where: List[str] = []
    args: List[Any] = []
    if category:
        where.append("category = ?")
        args.append(category)
    if calc_id:
        where.append("calc_id = ?")
        args.append(calc_id)
    if since is not None:
        where.append("ts >= ?")
        args.append(since)
    if until is not None:
        where.append("ts <= ?")
        args.append(until)
    where_clause = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""SELECT * FROM calc_history
              {where_clause}
              ORDER BY ts DESC, id DESC
              LIMIT ? OFFSET ?"""
    args.extend([limit, offset])
    start = time.perf_counter()
    with _connect() as conn:
        rows = conn.execute(sql, args).fetchall()
    elapsed = (time.perf_counter() - start) * 1000
    _logger.debug(
        f"[READ] op=list_records limit={limit} offset={offset} "
        f"category={category!r} calc_id={calc_id!r} returned={len(rows)} "
        f"elapsed={elapsed:.3f}ms"
    )
    return [_row_to_dict(r) for r in rows]


def delete_record(record_id: int) -> bool:
    """删除单条. 返回是否实际删除."""
    start = _log_write_start('delete_record', record_id=record_id)
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM calc_history WHERE id = ?", (record_id,)
        )
        deleted = cur.rowcount > 0
    _log_write_end('delete_record', start, rowcount=cur.rowcount, deleted=deleted)
    return deleted


def delete_records(record_ids: Iterable[int]) -> int:
    """批量删除. 返回受影响行数."""
    ids = list(record_ids)
    if not ids:
        _logger.info("[WRITE-SKIP] op=delete_records reason=empty_ids")
        return 0
    start = _log_write_start('delete_records', count=len(ids), ids=ids[:20])
    placeholders = ",".join("?" * len(ids))
    with _connect() as conn:
        cur = conn.execute(
            f"DELETE FROM calc_history WHERE id IN ({placeholders})", ids
        )
        deleted = cur.rowcount
    _log_write_end('delete_records', start, requested=len(ids), deleted=deleted)
    return deleted


def count_records(category: Optional[str] = None) -> int:
    """统计记录数 (按 category 可选)."""
    with _connect() as conn:
        if category:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM calc_history WHERE category = ?",
                (category,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM calc_history"
            ).fetchone()
    return row['c']


def stats_by_category() -> Dict[str, int]:
    """按 category 分组统计."""
    with _connect() as conn:
        rows = conn.execute(
            """SELECT category, COUNT(*) AS c FROM calc_history
               GROUP BY category ORDER BY c DESC"""
        ).fetchall()
    return {r['category']: r['c'] for r in rows}


def clear_all() -> int:
    """清空全部. 返回删除行数 (供测试用)."""
    start = _log_write_start('clear_all')
    with _connect() as conn:
        cur = conn.execute("DELETE FROM calc_history")
        cleared = cur.rowcount
    _log_write_end('clear_all', start, cleared=cleared, status='ok')
    return cleared


def get_db_path() -> Optional[Path]:
    """返回当前数据库路径 (未初始化返回 None)."""
    return _db_path
