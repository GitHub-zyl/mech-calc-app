"""元信息端点: 健康检查/版本/分类树"""
from flask import Blueprint
from backend.api.responses import success

bp = Blueprint('meta', __name__, url_prefix='/api/meta')

APP_VERSION = '2.1.0'
APP_NAME = 'mech-design-calc'


@bp.get('/health')
def health():
    """健康检查"""
    return success({
        'app': APP_NAME,
        'version': APP_VERSION,
        'status': 'running',
    })


@bp.get('/version')
def version():
    """返回版本信息"""
    return success({
        'name': APP_NAME,
        'version': APP_VERSION,
    })


# 13 大类分类树 (来自 market-research, 对齐《机械设计手册》第五版)
CATEGORIES = [
    {'id': 'geometry',     'name_zh': '常用几何与数学',   'name_en': 'Geometry & Math',
     'icon': 'compass'},
    {'id': 'transmission', 'name_zh': '机械传动设计',     'name_en': 'Mechanical Transmission',
     'icon': 'cog'},
    {'id': 'shaft_system', 'name_zh': '轴系结构与强度',   'name_en': 'Shaft System & Strength',
     'icon': 'axis'},
    {'id': 'fasteners',    'name_zh': '紧固件与连接',     'name_en': 'Fasteners & Joints',
     'icon': 'screw'},
    {'id': 'tolerance',    'name_zh': '公差配合与形位',   'name_en': 'Tolerance & Fit',
     'icon': 'ruler'},
    {'id': 'materials',    'name_zh': '工程材料参数',     'name_en': 'Engineering Materials',
     'icon': 'beaker'},
    {'id': 'surface',      'name_zh': '表面与热处理',     'name_en': 'Surface & Heat Treatment',
     'icon': 'grid'},
    {'id': 'springs',      'name_zh': '弹簧设计',         'name_en': 'Spring Design',
     'icon': 'spring'},
    {'id': 'fluid',        'name_zh': '流体传动',         'name_en': 'Hydraulic & Pneumatic',
     'icon': 'droplet'},
    {'id': 'press',        'name_zh': '冲压与塑性成形',   'name_en': 'Press & Forming',
     'icon': 'hammer'},
    {'id': 'brake',        'name_zh': '制动器与离合器',   'name_en': 'Brake & Clutch',
     'icon': 'stop'},
    {'id': 'mechanics',    'name_zh': '力学与振动',       'name_en': 'Mechanics & Vibration',
     'icon': 'wave'},
    {'id': 'units',        'name_zh': '单位制与换算',     'name_en': 'Units & Conversion',
     'icon': 'scale'},
]


@bp.get('/categories')
def categories():
    """13 大类分类树"""
    return success(CATEGORIES)


@bp.get('/category/<cat_id>')
def category_detail(cat_id):
    """获取单个分类详情"""
    for c in CATEGORIES:
        if c['id'] == cat_id:
            return success(c)
    from backend.api.responses import error
    return error(f'未知分类: {cat_id}', code=404)
