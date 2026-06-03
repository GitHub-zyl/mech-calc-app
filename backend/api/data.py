"""材料/标准件/常数 数据 API

暴露 extracted_data.json 的全部数据 (材料/钢材/铝材/塑料/轴承/O型圈/螺纹)
以及 PHYSICAL_CONSTANTS 物理常数。

URL 前缀: /api/data
"""
from flask import Blueprint, request
from backend.config import Config
from backend.utils.db import load_json
from backend.utils.convert import safe_float
from backend.api.responses import success, error

bp = Blueprint('data', __name__, url_prefix='/api/data')

# 启动期预加载 (应用工厂已预热, 这里再保险一次)
DB = load_json(Config.DATA_FILE)

# 数据子类别清单 (用于前端导航/统计)
DATA_CATEGORIES = {
    'materials': '工程材料',
    'steel_grades': '钢材牌号',
    'aluminum_grades': '铝材牌号',
    'plastics': '塑料',
    'bearings': '深沟球轴承',
    'bearings_thrust': '推力轴承',
    'oring_groove': 'O型圈沟槽',
    'threads_metric': '公制螺纹',
    'threads_imperial': '英制螺纹',
    'constants': '物理常数',
}


@bp.get('/categories')
def categories():
    """数据子类别清单 + 各类别数量"""
    counts = {}
    for key in DATA_CATEGORIES:
        if key == 'constants':
            from backend.utils.units import PHYSICAL_CONSTANTS
            counts[key] = len(PHYSICAL_CONSTANTS)
        else:
            counts[key] = len(DB.get(key, []))
    return success(DATA_CATEGORIES, meta=counts)


# ---- 通用搜索 ----
def _search(items, q, name_keys=('name',)):
    """大小写不敏感搜索, 支持多字段"""
    if not q:
        return items
    q = q.lower()
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        for k in name_keys:
            v = item.get(k, '')
            if v and q in str(v).lower():
                out.append(item)
                break
    return out


# ---- 材料 ----
@bp.get('/materials')
def materials():
    """材料查询 (?q=搜索词, ?category=金属/非金属, ?limit=100)"""
    q = (request.args.get('q') or '').strip()
    category = (request.args.get('category') or '').strip()
    limit = int(request.args.get('limit', 100))

    items = DB.get('materials', [])
    if q:
        items = _search(items, q, name_keys=('name', 'category', 'application'))
    if category:
        items = [m for m in items if category in str(m.get('category', ''))]

    total = len(items)
    items = items[:max(1, min(limit, 500))]
    return success(items, meta={'total': total, 'returned': len(items)})


@bp.get('/materials/<name>')
def material_detail(name):
    """按名称精确查询"""
    for m in DB.get('materials', []):
        if m.get('name') == name:
            return success(m)
    return error(f'材料不存在: {name}', code=404)


# ---- 钢材/铝材/塑料 ----
@bp.get('/steel-grades')
def steel_grades():
    """钢材牌号 (?q=搜索)"""
    q = (request.args.get('q') or '').strip()
    items = DB.get('steel_grades', [])
    if q:
        items = _search(items, q, name_keys=('grade', 'name', 'application'))
    return success(items[:200], meta={'total': len(items), 'returned': min(200, len(items))})


@bp.get('/aluminum-grades')
def aluminum_grades():
    """铝材牌号"""
    q = (request.args.get('q') or '').strip()
    items = DB.get('aluminum_grades', [])
    if q:
        items = _search(items, q, name_keys=('grade', 'name'))
    return success(items[:200], meta={'total': len(items)})


@bp.get('/plastics')
def plastics():
    """塑料"""
    q = (request.args.get('q') or '').strip()
    items = DB.get('plastics', [])
    if q:
        items = _search(items, q, name_keys=('name', 'application'))
    return success(items[:200], meta={'total': len(items)})


# ---- 轴承 ----
@bp.get('/bearings')
def bearings():
    """深沟球轴承 (?q=型号, ?d=内径, ?D=外径)"""
    q = (request.args.get('q') or '').strip()
    d = safe_float(request.args.get('d'))
    items = DB.get('bearings_deep_groove', [])

    if q:
        items = _search(items, q, name_keys=('designation', 'series', 'd_mm'))
    if d is not None:
        # 找最接近内径
        items = sorted(items, key=lambda x: abs(safe_float(x.get('d_mm'), 0) - d))[:20]

    return success(items[:100], meta={'total': len(items)})


@bp.get('/bearings/thrust')
def bearings_thrust():
    """推力球轴承"""
    q = (request.args.get('q') or '').strip()
    items = DB.get('bearings_thrust', [])
    if q:
        items = _search(items, q, name_keys=('designation',))
    return success(items[:100], meta={'total': len(items)})


# ---- O 型圈 ----
@bp.get('/oring-groove')
def oring():
    """O 型圈沟槽尺寸 (?diameter=截面直径)"""
    sec = safe_float(request.args.get('diameter'))
    items = DB.get('oring_groove', [])
    if sec is not None:
        items = sorted(items, key=lambda x: abs(safe_float(x.get('section_diameter'), 0) - sec))[:10]
    return success(items)


# ---- 螺纹 ----
@bp.get('/threads/metric')
def threads_metric():
    """公制螺纹 (?spec=M12, ?nominal=12, ?pitch=1.75)"""
    spec = (request.args.get('spec') or '').strip()
    items = DB.get('threads_metric', [])
    if spec:
        items = [t for t in items if spec.upper() in str(t).upper()][:30]
    return success(items[:100], meta={'total': len(items)})


@bp.get('/threads/imperial')
def threads_imperial():
    """英制螺纹"""
    return success(DB.get('threads_imperial', [])[:100], meta={'total': len(DB.get('threads_imperial', []))})


# ---- 物理常数 ----
@bp.get('/constants')
def constants():
    """物理常数 (来自 utils.units.PHYSICAL_CONSTANTS)"""
    from backend.utils.units import PHYSICAL_CONSTANTS
    return success(PHYSICAL_CONSTANTS, meta={'count': len(PHYSICAL_CONSTANTS)})
