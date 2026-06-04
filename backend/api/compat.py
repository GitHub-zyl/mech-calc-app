"""旧路由兼容层 (Legacy URL Compatibility)

前端 (app.js, app-ext.js, app-ext2.js) 调用的 URL 与重构后的 v2 API 不一致:

旧路径                                  新路径
/api/calculate/<cat>/<name>     →     /api/calc/<cat>/<name>     (POST 计算)
/api/material/search?q=...      →     /api/data/materials?q=...  (GET  搜索)
/api/material/info?name=...     →     /api/data/materials/<name> (GET  详情)
/api/data/fit_recommendations   →     已迁移到 backend.api.p2_reference (Phase 2 实现)
/api/data/motor_knowledge       →     已迁移到 backend.api.p2_reference (Phase 2 实现)

本模块注册为单独的蓝图, 仅做路径转发和参数重命名,
不重复实现任何业务逻辑. Phase 1 完成后, 前端将统一迁移到新 API,
本蓝图保留至 Phase 2 末删除.
"""
from flask import Blueprint, request
from backend.api.responses import success, error

bp = Blueprint('compat', __name__)

# 路径前缀映射
_LEGACY_CALC_PREFIX = '/api/calculate/'
_NEW_CALC_PREFIX = '/api/calc/'


@bp.route('/api/calculate/<path:subpath>', methods=['GET', 'POST'])
def legacy_calculate(subpath):
    """/api/calculate/X/Y -> /api/calc/X/Y (内部转发, 复用相同 request body)"""
    new_path = _NEW_CALC_PREFIX + subpath
    if request.method == 'POST':
        # 复用现有测试客户端无法内部转发, 直接路由级 fallback:
        # 在测试中 test_client 不会真正发 HTTP, 而是直接调用 view function.
        # 这里通过 url_map 解析新路径, 然后用 test_client 的 environ 重新调用
        # 简化: 改由前端升级时直接使用新路径. 此处仅作 308 重定向.
        from flask import redirect
        return redirect(new_path, code=308)
    else:
        from flask import redirect
        return redirect(new_path, code=308)


@bp.route('/api/material/search', methods=['GET'])
def legacy_material_search():
    """/api/material/search?q=... -> /api/data/materials?q=..."""
    q = request.args.get('q', '')
    from flask import redirect
    return redirect(f'/api/data/materials?q={q}', code=308)


@bp.route('/api/material/info', methods=['GET'])
def legacy_material_info():
    """/api/material/info?name=X -> /api/data/materials/X"""
    name = request.args.get('name', '')
    from flask import redirect
    return redirect(f'/api/data/materials/{name}', code=308)


@bp.route('/api/data/fit_recommendations', methods=['GET'])
def legacy_fit_recommendations():
    """占位: 配合度推荐表 - 暂未在 v2 API 中实现, 返回空集合"""
    return success([], meta={'note': '配合度推荐表 - 计划在 Phase 2 实现'})


@bp.route('/api/data/motor_knowledge', methods=['GET'])
def legacy_motor_knowledge():
    """占位: 电机常识表 - 暂未在 v2 API 中实现, 返回空集合"""
    return success([], meta={'note': '电机常识 - 计划在 Phase 2 实现'})
