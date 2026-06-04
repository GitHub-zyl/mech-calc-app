"""P2 单元测试: data/p2_reference_data.py"""
import pytest
from backend.data import p2_reference_data as p2


# ============ 配合度推荐 ============

def test_fit_recommendations_nonempty():
    assert len(p2.FIT_RECOMMENDATIONS) >= 10


def test_fit_recommendations_unique_ids():
    ids = [f['id'] for f in p2.FIT_RECOMMENDATIONS]
    assert len(ids) == len(set(ids))


def test_get_fit_recommendations_all():
    items = p2.get_fit_recommendations()
    assert len(items) == len(p2.FIT_RECOMMENDATIONS)


def test_get_fit_recommendations_by_fit_type_clearance():
    items = p2.get_fit_recommendations(fit_type='间隙')
    assert all(f['fit_type'] == '间隙' for f in items)
    assert len(items) >= 3


def test_get_fit_recommendations_by_fit_type_transition():
    items = p2.get_fit_recommendations(fit_type='过渡')
    assert all(f['fit_type'] == '过渡' for f in items)
    assert len(items) >= 2


def test_get_fit_recommendations_by_fit_type_interference():
    items = p2.get_fit_recommendations(fit_type='过盈')
    assert all(f['fit_type'] == '过盈' for f in items)
    assert len(items) >= 2


def test_get_fit_recommendations_by_category():
    items = p2.get_fit_recommendations(category='滑动')
    assert all(f['category'] == '滑动' for f in items)


def test_get_fit_recommendations_combined():
    items = p2.get_fit_recommendations(fit_type='间隙', category='滑动')
    assert all(f['fit_type'] == '间隙' and f['category'] == '滑动' for f in items)


def test_get_fit_recommendations_empty_filter():
    items = p2.get_fit_recommendations(fit_type='不存在的类型')
    assert items == []


def test_fit_types():
    types = p2.get_fit_types()
    assert '间隙' in types
    assert '过渡' in types
    assert '过盈' in types


def test_fit_categories():
    cats = p2.get_fit_categories()
    assert '滑动' in cats


def test_fit_recommendations_have_required_fields():
    required = {'id', 'fit_type', 'category', 'hole', 'shaft',
                'application', 'min_clearance_mm', 'max_clearance_mm',
                'nominal_range_mm', 'examples', 'notes'}
    for f in p2.FIT_RECOMMENDATIONS:
        assert required.issubset(f.keys()), \
            f"配合 {f.get('id')} 缺少字段: {required - f.keys()}"


# ============ 电机常识 ============

def test_motor_knowledge_nonempty():
    assert len(p2.MOTOR_KNOWLEDGE) >= 20


def test_motor_knowledge_unique_ids():
    ids = [k['id'] for k in p2.MOTOR_KNOWLEDGE]
    assert len(ids) == len(set(ids))


def test_get_motor_knowledge_all():
    items = p2.get_motor_knowledge()
    assert len(items) == len(p2.MOTOR_KNOWLEDGE)


def test_get_motor_knowledge_by_category():
    for cat in ['类型', '起动', '调速', '制动', '保护', '铭牌', '防护', '绝缘', '转速']:
        items = p2.get_motor_knowledge(category=cat)
        assert all(k['category'] == cat for k in items)
        assert len(items) >= 1, f"分类 {cat} 无数据"


def test_get_motor_categories():
    cats = p2.get_motor_categories()
    assert '铭牌' in cats
    assert '起动' in cats
    assert '制动' in cats


def test_motor_knowledge_have_required_fields():
    required = {'id', 'name_zh', 'name_en', 'category', 'description'}
    for k in p2.MOTOR_KNOWLEDGE:
        assert required.issubset(k.keys()), \
            f"电机 {k.get('id')} 缺少字段: {required - k.keys()}"


def test_motor_knowledge_has_50hz_speed():
    """必须有 50Hz 同步转速数据"""
    items = p2.get_motor_knowledge(category='转速')
    speed_ids = {it['id'] for it in items}
    assert 'motor_sync_speed_50hz_4p' in speed_ids
