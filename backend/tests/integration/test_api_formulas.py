"""集成测试: /api/formulas REST 接口"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()


# ============ 列表 ============

def test_list_all(client):
    r = client.get('/api/formulas')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert j['data']['total'] > 0
    assert len(j['data']['items']) == j['data']['total']


def test_list_filter_by_category(client):
    r = client.get('/api/formulas?category=mechanics')
    j = r.get_json()
    assert j['status'] == 'ok'
    for item in j['data']['items']:
        assert item['category'] == 'mechanics'


def test_list_filter_by_q_id(client):
    r = client.get('/api/formulas?q=fma')
    j = r.get_json()
    assert any(it['id'] == 'fma' for it in j['data']['items'])


def test_list_filter_by_q_zh(client):
    """按中文名搜索"""
    r = client.get('/api/formulas?q=牛顿')
    j = r.get_json()
    assert any(it['id'] == 'fma' for it in j['data']['items'])


def test_list_filter_by_q_tag(client):
    """按标签搜索"""
    r = client.get('/api/formulas?q=动力学')
    j = r.get_json()
    assert any(it['id'] == 'fma' for it in j['data']['items'])


def test_list_q_and_category_combined(client):
    r = client.get('/api/formulas?q=圆&category=geometry')
    j = r.get_json()
    assert all(it['category'] == 'geometry' for it in j['data']['items'])


def test_list_no_match(client):
    r = client.get('/api/formulas?q=zzzzzz_no_match')
    j = r.get_json()
    assert j['data']['items'] == []
    assert j['data']['total'] == 0


# ============ 分类清单 ============

def test_categories(client):
    r = client.get('/api/formulas/categories')
    assert r.status_code == 200
    cats = r.get_json()['data']
    assert 'mechanics' in cats
    assert 'energy' in cats
    assert 'geometry' in cats
    assert cats == sorted(cats)


# ============ 详情 ============

def test_detail_success(client):
    r = client.get('/api/formulas/fma')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert j['data']['id'] == 'fma'
    assert j['data']['name_zh'] == '牛顿第二定律'
    assert 'F' in j['data']['variables']
    assert 'm' in j['data']['variables']
    assert 'a' in j['data']['variables']


def test_detail_not_found(client):
    r = client.get('/api/formulas/not_a_real_id')
    assert r.status_code == 404
    j = r.get_json()
    assert j['status'] == 'error'


# ============ 相关公式 ============

def test_related_success(client):
    r = client.get('/api/formulas/fma/related')
    assert r.status_code == 200
    j = r.get_json()
    assert j['data']['formula_id'] == 'fma'
    assert len(j['data']['related']) >= 1
    ids = {x['id'] for x in j['data']['related']}
    assert 'pfa' in ids


def test_related_not_found(client):
    r = client.get('/api/formulas/xxx_yyy/related')
    assert r.status_code == 404


def test_related_empty(client):
    """无 related 字段的公式应返回空列表"""
    # 找一个没有 related 的公式
    all_r = client.get('/api/formulas')
    target = None
    for it in all_r.get_json()['data']['items']:
        if not it.get('related'):
            target = it['id']
            break
    if target is None:
        pytest.skip("无测试目标 (所有公式都有 related)")
    r = client.get(f'/api/formulas/{target}/related')
    assert r.status_code == 200
    assert r.get_json()['data']['related'] == []


# ============ 求解 ============

def test_solve_success(client):
    """F = m·a, 已知 m=10, a=2 求 F=20"""
    r = client.post('/api/formulas/fma/solve', json={
        'given': {'m': 10, 'a': 2}
    })
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert j['data']['target'] == 'F'
    assert abs(j['data']['value'] - 20) < 1e-9


def test_solve_with_default(client):
    """pfg 重力公式, g 有默认值 9.81"""
    r = client.post('/api/formulas/pfg/solve', json={
        'given': {'m': 10}
    })
    assert r.status_code == 200
    j = r.get_json()
    assert j['data']['target'] == 'G'
    assert abs(j['data']['value'] - 98.1) < 1e-6


def test_solve_missing_vars(client):
    """已知量不足"""
    r = client.post('/api/formulas/fma/solve', json={
        'given': {'m': 10}
    })
    assert r.status_code == 400
    j = r.get_json()
    assert j['status'] == 'error'
    assert 'details' in j
    assert 'F' in j['details'] and 'a' in j['details']


def test_solve_formula_not_exists(client):
    r = client.post('/api/formulas/xxx_yyy/solve', json={
        'given': {'a': 1}
    })
    assert r.status_code == 404


def test_solve_invalid_given_type(client):
    """given 不是 dict"""
    r = client.post('/api/formulas/fma/solve', json={
        'given': 'not a dict'
    })
    assert r.status_code == 400


def test_solve_invalid_value_type(client):
    """given 中的值无法转 float"""
    r = client.post('/api/formulas/fma/solve', json={
        'given': {'m': 'not a number', 'a': 2}
    })
    assert r.status_code == 400


def test_solve_no_body(client):
    """空 body"""
    r = client.post('/api/formulas/fma/solve',
                    data='', content_type='application/json')
    assert r.status_code == 400


def test_solve_empty_given(client):
    """given 为空 dict"""
    r = client.post('/api/formulas/fma/solve', json={'given': {}})
    assert r.status_code == 400


def test_solve_with_extra_unknown_keys(client):
    """given 包含非公式变量 → 自动忽略"""
    r = client.post('/api/formulas/fma/solve', json={
        'given': {'m': 10, 'a': 2, 'extra': 999}
    })
    assert r.status_code == 200
    j = r.get_json()
    assert abs(j['data']['value'] - 20) < 1e-9


def test_solve_skip_none_values(client):
    """given 中包含 None → 跳过 (避免转换错误)"""
    r = client.post('/api/formulas/fma/solve', json={
        'given': {'m': None, 'a': 2}
    })
    # m=None 被跳过, 缺 m
    assert r.status_code == 400
    j = r.get_json()
    assert 'details' in j
    assert 'm' in j['details']


# ============ 边界 ============

def test_response_shape_consistency(client):
    """所有成功响应都包含 status=ok + data"""
    for url in ['/api/formulas', '/api/formulas/fma',
                '/api/formulas/categories', '/api/formulas/fma/related']:
        r = client.get(url)
        j = r.get_json()
        assert j['status'] == 'ok', f"{url} 响应异常"
        assert 'data' in j, f"{url} 缺少 data 字段"


def test_404_response_shape(client):
    """错误响应包含 status=error + code + message"""
    r = client.get('/api/formulas/no_such_id')
    j = r.get_json()
    assert j['status'] == 'error'
    assert j['code'] == 404
    assert 'message' in j
