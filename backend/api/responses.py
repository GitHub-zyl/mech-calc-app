"""统一 API 响应格式

约定:
- success(data, meta=None, status=200) → Response(JSON {status:'ok', data, [meta]})
- error(message, code=400, details=None) → Response(JSON {status:'error', message, code, [details]})
"""
from flask import jsonify


def success(data, meta=None, status=200):
    """构造成功响应, 返回 Flask Response 对象

    Args:
        data: 业务数据, 可为 dict/list/str/None
        meta: 附加元信息 (如 total/returned/duration)
        status: HTTP 状态码, 默认 200
    """
    body = {'status': 'ok', 'data': data}
    if meta is not None:
        body['meta'] = meta
    resp = jsonify(body)
    resp.status_code = status
    return resp


def error(message, code=400, details=None):
    """构造错误响应, 返回 Flask Response 对象

    Args:
        message: 错误描述(用户可读)
        code: HTTP 状态码 (400/404/422/500 等)
        details: 附加结构化错误信息
    """
    body = {'status': 'error', 'message': str(message), 'code': code}
    if details is not None:
        body['details'] = details
    resp = jsonify(body)
    resp.status_code = code
    return resp
