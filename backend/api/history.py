"""REST 风格的 /api/history 蓝图

Endpoints:
    GET    /api/history              - 列表 (分页+筛选)
    GET    /api/history/<id>         - 详情
    POST   /api/history              - 新增
    DELETE /api/history/<id>         - 删除单条
    DELETE /api/history              - 批量删除 (?ids=1,2,3 或清空)
    GET    /api/history/stats        - 统计 (总数+分类)
    GET    /api/history/categories   - 已有分类清单 (派生自数据)
"""
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.database import (
    add_record, get_record, list_records, delete_record,
    delete_records, count_records, stats_by_category, clear_all,
)
from backend.utils.convert import safe_float, safe_int

bp = Blueprint('history', __name__, url_prefix='/api/history')


def _client_ip() -> str:
    return request.headers.get('X-Forwarded-For', request.remote_addr or '')[:45]


@bp.get('')
@bp.get('/')
def list_view():
    """GET /api/history?limit=&offset=&category=&calc_id=&since=&until="""
    try:
        limit = max(1, min(200, int(request.args.get('limit', 20))))
        offset = max(0, int(request.args.get('offset', 0)))
    except (TypeError, ValueError):
        return error('limit/offset 必须为整数', code=400)

    category = request.args.get('category') or None
    calc_id = request.args.get('calc_id') or None
    since = safe_float(request.args.get('since'))
    until = safe_float(request.args.get('until'))

    items = list_records(limit=limit, offset=offset, category=category,
                         calc_id=calc_id, since=since, until=until)
    total = count_records(category=category)
    return success({
        'items': items,
        'pagination': {
            'limit': limit,
            'offset': offset,
            'total': total,
            'has_more': (offset + len(items)) < total,
        },
    })


@bp.post('')
@bp.post('/')
def add_view():
    """POST /api/history
    Body:
        {
            "category": "gear",
            "endpoint": "/api/calc/gear/spur",
            "calc_id": "gear-spur",
            "input": {...},
            "output": {...},
            "duration_ms": 1.2   # 可选
        }
    """
    data = request.get_json(silent=True) or {}
    category = (data.get('category') or '').strip()
    endpoint = (data.get('endpoint') or '').strip()
    if not category or not endpoint:
        return error('category 和 endpoint 必填', code=400)
    if 'input' not in data or 'output' not in data:
        return error('input 和 output 必填', code=400)
    try:
        rid = add_record(
            category=category,
            endpoint=endpoint,
            input_data=data['input'],
            output_data=data['output'],
            calc_id=data.get('calc_id'),
            client_ip=_client_ip(),
            duration_ms=safe_float(data.get('duration_ms')),
        )
    except ValueError as e:
        return error(str(e), code=400)
    rec = get_record(rid)
    return success({'id': rid, 'record': rec}, meta={'created': True})


@bp.get('/<int:rid>')
def detail_view(rid):
    rec = get_record(rid)
    if not rec:
        return error(f'记录 {rid} 不存在', code=404)
    return success(rec)


@bp.delete('/<int:rid>')
def delete_view(rid):
    ok = delete_record(rid)
    if not ok:
        return error(f'记录 {rid} 不存在', code=404)
    return success({'id': rid, 'deleted': True})


@bp.delete('')
@bp.delete('/')
def delete_batch_view():
    """DELETE /api/history?ids=1,2,3  或  ?all=1 (清空)"""
    if request.args.get('all') == '1':
        n = clear_all()
        return success({'cleared': n})
    ids_str = request.args.get('ids', '')
    if not ids_str:
        return error('请提供 ids=1,2,3 或 all=1', code=400)
    try:
        ids = [int(s) for s in ids_str.split(',') if s.strip()]
    except ValueError:
        return error('ids 格式错误, 应为逗号分隔整数', code=400)
    n = delete_records(ids)
    return success({'requested': len(ids), 'deleted': n})


@bp.get('/stats')
def stats_view():
    """GET /api/history/stats"""
    return success({
        'total': count_records(),
        'by_category': stats_by_category(),
    })


@bp.get('/categories')
def categories_view():
    """GET /api/history/categories - 实际存储中出现的分类"""
    cats = list(stats_by_category().keys())
    return success(cats)
