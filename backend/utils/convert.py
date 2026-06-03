"""类型转换工具"""
from typing import Any


def safe_float(v: Any, default=None):
    """安全转换为 float, 失败返回 default

    用于 HTTP 请求参数解析, 避免 ValueError 上浮。
    """
    if v is None or v == '':
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def safe_int(v: Any, default=None):
    """安全转换为 int, 失败返回 default"""
    if v is None or v == '':
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        f = safe_float(v)
        return int(f) if f is not None else default
