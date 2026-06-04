"""REST 风格的 /api/formulas 蓝图

Endpoints:
    GET  /api/formulas                - 列表 (?q=&category=)
    GET  /api/formulas/categories     - 分类清单
    GET  /api/formulas/<id>           - 详情
    GET  /api/formulas/<id>/related   - 相关公式
    POST /api/formulas/<id>/solve     - 求解 (body: {"given": {...}})
"""
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.calculations.formulas_data import (
    get_all, get_by_id, get_categories, search, get_related, solve,
)

bp = Blueprint('formulas', __name__, url_prefix='/api/formulas')


@bp.get('')
@bp.get('/')
def list_view():
    q = request.args.get('q', '').strip()
    category = request.args.get('category') or None
    items = search(q, category=category)
    return success({
        'items': items,
        'total': len(items),
        'q': q,
        'category': category,
    })


@bp.get('/categories')
def categories_view():
    cats = get_categories()
    return success(cats)


@bp.get('/<fid>')
def detail_view(fid):
    f = get_by_id(fid)
    if not f:
        return error(f'公式 {fid} 不存在', code=404)
    return success(f)


@bp.get('/<fid>/related')
def related_view(fid):
    f = get_by_id(fid)
    if not f:
        return error(f'公式 {fid} 不存在', code=404)
    return success({
        'formula_id': fid,
        'related': get_related(fid),
    })


@bp.post('/<fid>/solve')
def solve_view(fid):
    """POST /api/formulas/<id>/solve
    Body: { "given": {"m": 10, "a": 2} }
    """
    f = get_by_id(fid)
    if not f:
        return error(f'公式 {fid} 不存在', code=404)
    data = request.get_json(silent=True) or {}
    given = data.get('given', {})
    if not isinstance(given, dict):
        return error('given 必须为 dict', code=400)
    # 转换值为 float
    try:
        given_f = {k: float(v) for k, v in given.items() if v is not None}
    except (TypeError, ValueError) as e:
        return error(f'given 数值转换失败: {e}', code=400)
    result = solve(fid, given_f)
    if not result.get('ok'):
        return error(result.get('error', '求解失败'), code=400,
                     details=result.get('missing'))
    return success(result)
