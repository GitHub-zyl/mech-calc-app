"""数据库 (JSON) 加载与缓存

设计要点:
- 单次加载, 线程安全, 后续请求直接命中内存
- 启动期调 load_json() 预热, 避免首请求卡顿
- 测试/热重载可用 clear_cache() 强制重读
"""
import json
from pathlib import Path
from threading import Lock

_lock = Lock()
_cache: dict = {}


def load_json(path):
    """加载 JSON, 命中缓存直接返回同一对象

    Args:
        path: Path 或 str (Path-like)

    Returns:
        dict/list: 解析后的 JSON 数据
    """
    p = Path(path)
    key = str(p.resolve()) if p.exists() else str(p)

    if key in _cache:
        return _cache[key]

    with _lock:
        if key in _cache:
            return _cache[key]
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _cache[key] = data
        return data


def clear_cache(path=None):
    """清空缓存

    Args:
        path: 指定路径时只清该条; None 清空全部
    """
    with _lock:
        if path is None:
            _cache.clear()
        else:
            p = Path(path)
            key = str(p.resolve()) if p.exists() else str(p)
            _cache.pop(key, None)


def cache_size():
    """返回当前缓存条目数 (用于调试)"""
    return len(_cache)
