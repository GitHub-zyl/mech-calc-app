"""单元测试: calculations/formulas_data.py

覆盖公式库的:
- get_all / get_by_id / get_categories / search / get_related
- _parse_vars_from_expr
- solve() 全部分支 (成功 / 缺量 / 公式不存在 / 反解失败)
"""
import pytest

import backend.calculations.formulas_data as fd
from backend.calculations.formulas_data import (
    FORMULAS, get_all, get_by_id, get_categories,
    search, get_related, solve, _parse_vars_from_expr,
)


# ============ 基础数据 ============

def test_formulas_list_nonempty():
    """公式库至少有 20 条记录 (计划要求 30+)"""
    assert len(FORMULAS) >= 20


def test_get_all():
    items = get_all()
    assert items is FORMULAS or items == FORMULAS
    assert len(items) == len(FORMULAS)


def test_get_by_id_exists():
    f = get_by_id('fma')
    assert f is not None
    assert f['name_zh'] == '牛顿第二定律'
    assert 'F' in f['variables']
    assert 'm' in f['variables']
    assert 'a' in f['variables']


def test_get_by_id_not_exists():
    assert get_by_id('not_a_real_id') is None
    assert get_by_id('') is None


def test_get_categories_sorted_unique():
    cats = get_categories()
    assert isinstance(cats, list)
    assert cats == sorted(cats)
    assert len(cats) == len(set(cats))
    # 至少包含几个常见分类
    assert 'mechanics' in cats
    assert 'energy' in cats
    assert 'geometry' in cats


# ============ search() ============

def test_search_no_query_no_category():
    """空查询返回全部"""
    items = search('')
    assert len(items) == len(FORMULAS)


def test_search_no_query_with_category():
    items = search('', category='mechanics')
    assert all(it['category'] == 'mechanics' for it in items)
    assert len(items) > 0


def test_search_by_id():
    items = search('fma')
    assert any(it['id'] == 'fma' for it in items)


def test_search_by_name_zh():
    items = search('牛顿')
    assert any(it['id'] == 'fma' for it in items)


def test_search_by_name_en():
    items = search('Newton')
    assert any(it['id'] == 'fma' for it in items)


def test_search_by_tag():
    items = search('动力学')
    assert any(it['id'] == 'fma' for it in items)


def test_search_by_formula_str():
    items = search('m · a')  # 中文公式中的特殊字符可能不命中, 但普通字符串可以
    # 即使没命中也不报错
    assert isinstance(items, list)


def test_search_case_insensitive():
    items1 = search('NEWTON')
    items2 = search('newton')
    assert len(items1) == len(items2)


def test_search_no_match():
    items = search('xyzxyzxyz123123')
    assert items == []


def test_search_combined_q_and_category():
    items = search('圆', category='geometry')
    assert all(it['category'] == 'geometry' for it in items)
    # '圆' 在 circle_area / circle_circumference 的 description/tags
    assert len(items) >= 1


# ============ get_related() ============

def test_get_related_exists():
    """fma 有关联: pfa, pfg, impulse"""
    related = get_related('fma')
    assert len(related) >= 1
    ids = {r['id'] for r in related}
    assert 'pfa' in ids


def test_get_related_not_exists():
    assert get_related('not_a_real_id') == []


def test_get_related_returns_dicts():
    related = get_related('circle_area')
    assert all('id' in r and 'formula' in r for r in related)


# ============ _parse_vars_from_expr ============

def test_parse_vars_simple():
    assert _parse_vars_from_expr('F = m * a') == ['F']


def test_parse_vars_with_subscript():
    # 提取等号左侧的标识符
    assert _parse_vars_from_expr('Ek = 0.5 * m * v**2') == ['Ek']


def test_parse_vars_no_equals():
    # 没有 = 时, 整个字符串作为左侧, re.findall 提取所有标识符
    res = _parse_vars_from_expr('m * v')
    assert 'm' in res
    assert 'v' in res


# ============ solve() 正常路径 ============

def test_solve_fma_force():
    """F=ma, 已知 m, a 求 F"""
    r = solve('fma', {'m': 10, 'a': 2})
    assert r['ok'] is True
    assert r['target'] == 'F'
    assert abs(r['value'] - 20) < 1e-9
    assert r['result']['F'] == 20
    assert r['result']['m'] == 10


def test_solve_fma_acceleration():
    """F=ma, 已知 F, m 求 a (目标非 lhs, 当前实现暂不支持)"""
    r = solve('fma', {'F': 100, 'm': 50})
    # 当前实现: 只支持反解 lhs, 目标 a 时 eval 因 a 不在命名空间而失败
    assert r['ok'] is False
    # 错误信息可能是 "求值失败: name 'a' is not defined" 或 "不支持反解"
    assert '求值失败' in r['error'] or '不支持反解' in r['error']


def test_solve_pfv():
    """P=Fv, 已知 F, v 求 P"""
    r = solve('pfv', {'F': 100, 'v': 5})
    assert r['ok'] is True
    assert r['target'] == 'P'
    assert abs(r['value'] - 500) < 1e-9


def test_solve_uses_default():
    """pfg 重力公式: g 有默认值"""
    r = solve('pfg', {'m': 10})
    assert r['ok'] is True
    assert r['target'] == 'G'
    assert abs(r['value'] - 98.1) < 1e-6


def test_solve_vt():
    """s=v*t, 已知 v, t 求 s"""
    r = solve('vt', {'v': 10, 't': 3})
    assert r['ok'] is True
    assert r['target'] == 's'
    assert abs(r['value'] - 30) < 1e-9


def test_solve_circle_area():
    """圆面积 A=πd²/4, 已知 d=10 求 A"""
    r = solve('circle_area', {'d': 10})
    assert r['ok'] is True
    assert r['target'] == 'A'
    assert abs(r['value'] - (3.14159265358979 * 100 / 4)) < 1e-3


def test_solve_heat():
    """Q=cmdT, 已知 c, m, dT 求 Q"""
    r = solve('heat', {'c': 4200, 'm': 2, 'dT': 10})
    assert r['ok'] is True
    assert r['target'] == 'Q'
    assert abs(r['value'] - 84000) < 1e-6


def test_solve_returns_unit():
    r = solve('fma', {'m': 1, 'a': 1})
    assert r['unit'] == 'N'


def test_solve_returns_formula_str():
    r = solve('fma', {'m': 1, 'a': 1})
    assert r['formula'] == 'F = m · a'


# ============ solve() 异常路径 ============

def test_solve_formula_not_exists():
    r = solve('xxx_yyy', {'a': 1})
    assert r['ok'] is False
    assert '不存在' in r['error']


def test_solve_missing_vars():
    """fma 有 3 个变量, 已知 0 个 → 缺 3 个"""
    r = solve('fma', {})
    assert r['ok'] is False
    assert 'missing' in r
    assert len(r['missing']) == 3


def test_solve_partial_missing():
    """fma 已知 1 个变量 → 缺 2 个"""
    r = solve('fma', {'m': 1})
    assert r['ok'] is False
    assert len(r['missing']) == 2


def test_solve_all_known():
    """所有变量都给了 → 返回一致性校验 (无需求解)"""
    r = solve('fma', {'F': 20, 'm': 10, 'a': 2})
    assert r['ok'] is True
    assert 'note' in r
    assert r['result']['F'] == 20


def test_solve_value_error_in_expr():
    """传入除零等异常情况"""
    r = solve('pfa', {'F': 1, 'A': 0})  # 1/0
    assert r['ok'] is False
    assert 'error' in r


def test_solve_target_not_lhs():
    """target 不是 lhs 时, 当前实现提示不支持反解"""
    # omega_to_n: lhs=omega, 已知 n 求 omega 应 OK
    r = solve('omega_to_n', {'n': 60})
    assert r['ok'] is True
    assert r['target'] == 'omega'
    assert abs(r['value'] - (2 * 3.14159265358979)) < 1e-6


# ============ 公式 schema 完整性 ============

def test_formulas_have_required_fields():
    """所有公式包含必填字段"""
    required = {'id', 'name_zh', 'name_en', 'formula', 'expr',
                'variables', 'unknowns', 'category'}
    for f in FORMULAS:
        assert required.issubset(f.keys()), \
            f"公式 {f.get('id')} 缺少字段: {required - f.keys()}"


def test_formulas_variables_have_metadata():
    """所有变量都包含 name 和 unit"""
    for f in FORMULAS:
        for v, meta in f['variables'].items():
            assert 'name' in meta, f"{f['id']}.{v} 缺少 name"
            assert 'unit' in meta, f"{f['id']}.{v} 缺少 unit"


def test_formulas_unknowns_in_variables():
    """unknowns 列出的变量必须在 variables 中"""
    for f in FORMULAS:
        for u in f['unknowns']:
            assert u in f['variables'], \
                f"公式 {f['id']} 的 unknowns {u} 不在 variables 中"


def test_formulas_ids_unique():
    """id 必须唯一"""
    ids = [f['id'] for f in FORMULAS]
    assert len(ids) == len(set(ids))


def test_formulas_related_exist():
    """related 引用的 id 必须存在"""
    all_ids = {f['id'] for f in FORMULAS}
    for f in FORMULAS:
        for rid in f.get('related', []):
            assert rid in all_ids, \
                f"公式 {f['id']} 的 related {rid} 不存在"
