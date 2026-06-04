"""计算历史 SQLite 持久化模块

设计要点:
- 单例 DB 路径, 通过 init_db() 初始化表结构
- 使用 WAL 模式提升并发读
- 所有写操作使用事务
- 输入/输出以 JSON 字符串存储, 灵活支持嵌套结构
- 提供 list / get / add / delete / count / clear / stats 全套 CRUD
- 所有数据写入操作均带有结构化日志 (写入前/写入后 + 耗时)

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


def init_db(db_path: str | Path) -> Path:
    """初始化数据库. 多次调用是幂等的."""
    global _db_path, _initialized
    start = _log_write_start('init_db', db_path=str(db_path))
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        _db_path = p
        with _connect() as conn:
            conn.executescript(_SCHEMA)
            # 启用 WAL 模式提升并发
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
        _initialized = True
    _log_write_end('init_db', start, path=str(p), initialized=True)
    return p


@contextmanager
def _connect():
    """获取连接 (短连接模式, 简单可靠)."""
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
