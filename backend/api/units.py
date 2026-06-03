"""单位换算 API

URL 前缀: /api/units
"""
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.utils.units import (
    convert_all, list_categories, format_value, PHYSICAL_CONSTANTS,
)

bp = Blueprint('units', __name__, url_prefix='/api/units')


def _parse_payload(d):
    """从请求 JSON 提取换算参数"""
    value = d.get('value')
    from_u = d.get('from', '')
    to_u = d.get('to', '')
    category = d.get('category', 'length')
    return value, from_u, to_u, category


@bp.get('/categories')
def categories():
    """列出所有单位类别和可用单位 (前端用来构建下拉框)"""
    return success(list_categories())


@bp.get('/category/<category_id>')
def category_detail(category_id):
    """单个类别详情"""
    for c in list_categories():
        if c['id'] == category_id:
            return success(c)
    return error(f'未知单位类别: {category_id}', code=404)


@bp.post('/convert')
def convert():
    """通用单位换算

    Request JSON:
    {
        "value": 1,
        "from": "m",
        "to": "mm",
        "category": "length"
    }

    Response:
    {
        "status": "ok",
        "data": {
            "value": 1000.0,         # 换算结果
            "formatted": "1000",
            "from": "m",
            "to": "mm",
            "category": "长度",
            "input_value": 1.0
        }
    }
    """
    d = request.get_json(silent=True) or {}
    value, from_u, to_u, category = _parse_payload(d)

    if value is None:
        return error('请提供 value', code=400)
    if not from_u or not to_u:
        return error('请提供 from 和 to', code=400)
    if not category:
        return error('请提供 category', code=400)

    try:
        value = float(value)
    except (TypeError, ValueError):
        return error('value 必须是数字', code=400)

    result = convert_all(value, from_u, to_u, category)

    # convert_all 在错误时返回 {'error': '...'}
    if isinstance(result, dict) and 'error' in result:
        return error(result['error'], code=400,
                     details={'category': category, 'from': from_u, 'to': to_u})

    # 正常情况: 提取数值
    numeric_result = result['result'] if isinstance(result, dict) else result
    return success({
        'value': numeric_result,
        'formatted': format_value(numeric_result),
        'from': from_u,
        'to': to_u,
        'category': category,
        'input_value': value,
    })


@bp.post('/convert/batch')
def convert_batch():
    """批量换算, 一次性算多组值

    Request JSON:
    {
        "items": [
            {"value": 1, "from": "m", "to": "mm", "category": "length"},
            ...
        ]
    }
    """
    d = request.get_json(silent=True) or {}
    items = d.get('items', [])
    if not isinstance(items, list) or not items:
        return error('items 必须是非空列表', code=400)

    results = []
    for i, item in enumerate(items):
        value, from_u, to_u, category = _parse_payload(item)
        try:
            v = float(value)
            r = convert_all(v, from_u, to_u, category)
            if isinstance(r, dict) and 'error' in r:
                results.append({'index': i, 'ok': False, 'error': r['error']})
            else:
                num = r['result'] if isinstance(r, dict) else r
                results.append({'index': i, 'ok': True, 'value': num,
                                'from': from_u, 'to': to_u, 'category': category})
        except Exception as e:
            results.append({'index': i, 'ok': False, 'error': str(e)})

    success_count = sum(1 for r in results if r['ok'])
    return success(results, meta={'count': len(results), 'success': success_count})


@bp.get('/constants')
def constants():
    """物理常数 (来自 utils.units.PHYSICAL_CONSTANTS)"""
    return success(PHYSICAL_CONSTANTS, meta={'count': len(PHYSICAL_CONSTANTS)})
