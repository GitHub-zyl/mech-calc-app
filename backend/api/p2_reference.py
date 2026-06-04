"""P2 任务: 实现 fit_recommendations + motor_knowledge 端点

实现 Phase 1 文档中标记为占位的两个端点:
- GET /api/data/fit_recommendations  →  配合度推荐表
- GET /api/data/motor_knowledge      →  电机常识表

来源: 机械设计手册 (GB/T 1800.1, GB 755, GB 4208 等)
"""
import logging
import time
from flask import Blueprint, request

from backend.api.responses import success
from backend.data.p2_reference_data import (
    FIT_RECOMMENDATIONS, MOTOR_KNOWLEDGE,
    get_fit_recommendations, get_motor_knowledge,
    get_motor_categories, get_fit_categories, get_fit_types,
)


_logger = logging.getLogger('backend.api.p2_reference')
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s] [%(threadName)s(tid=%(thread)d)] %(message)s'
    ))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


bp = Blueprint('p2_reference', __name__)


# ============== 配合度推荐表 ==============

@bp.route('/api/data/fit_recommendations', methods=['GET'])
def fit_recommendations_list():
    """配合度推荐表 (Phase 2 实现, 替代 compat 层的空占位).

    Query 参数:
        fit_type: 间隙/过渡/过盈
        category: 滑动/轻过盈/...
    """
    start = time.perf_counter()
    fit_type = request.args.get('fit_type', '').strip() or None
    category = request.args.get('category', '').strip() or None
    items = get_fit_recommendations(fit_type=fit_type, category=category)
    elapsed = (time.perf_counter() - start) * 1000
    _logger.info(
        f"[LOAD-START] trigger=fit_recommendations ts={time.time():.6f} "
        f"fit_type={fit_type!r} category={category!r}"
    )
    _logger.info(
        f"[LOAD-END]   trigger=fit_recommendations elapsed={elapsed:.3f}ms "
        f"hits={len(items)}/{len(FIT_RECOMMENDATIONS)} status=ok"
    )
    return success({
        'items': items,
        'total': len(FIT_RECOMMENDATIONS),
        'filtered': len(items),
        'fit_types': get_fit_types(),
        'categories': get_fit_categories(),
        'note': 'Phase 2 实现 - 数据源 GB/T 1800.1-2009',
    })


@bp.route('/api/data/fit_recommendations/<fit_id>', methods=['GET'])
def fit_recommendations_detail(fit_id):
    """配合度推荐详情 (按 id 查)."""
    for f in FIT_RECOMMENDATIONS:
        if f['id'] == fit_id:
            return success(f)
    from backend.api.responses import error
    return error(f'配合 {fit_id} 不存在', code=404)


# ============== 电机常识表 ==============

@bp.route('/api/data/motor_knowledge', methods=['GET'])
def motor_knowledge_list():
    """电机常识表 (Phase 2 实现).

    Query 参数:
        category: 类型/起动/调速/制动/保护/铭牌/防护/绝缘/转速
    """
    start = time.perf_counter()
    category = request.args.get('category', '').strip() or None
    items = get_motor_knowledge(category=category)
    elapsed = (time.perf_counter() - start) * 1000
    _logger.info(
        f"[LOAD-START] trigger=motor_knowledge ts={time.time():.6f} "
        f"category={category!r}"
    )
    _logger.info(
        f"[LOAD-END]   trigger=motor_knowledge elapsed={elapsed:.3f}ms "
        f"hits={len(items)}/{len(MOTOR_KNOWLEDGE)} status=ok"
    )
    return success({
        'items': items,
        'total': len(MOTOR_KNOWLEDGE),
        'filtered': len(items),
        'categories': get_motor_categories(),
        'note': 'Phase 2 实现 - 数据源 GB 755/GB 4208/GB 11021',
    })


@bp.route('/api/data/motor_knowledge/<kid>', methods=['GET'])
def motor_knowledge_detail(kid):
    """电机常识详情."""
    for k in MOTOR_KNOWLEDGE:
        if k['id'] == kid:
            return success(k)
    from backend.api.responses import error
    return error(f'电机常识 {kid} 不存在', code=404)
