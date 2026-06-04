"""旧路由兼容层集成测试"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_legacy_calculate_redirects(client):
    """/api/calculate/X -> /api/calc/X (308 永久重定向)"""
    r = client.post('/api/calculate/belt/vbelt', json={'a': 1}, follow_redirects=False)
    assert r.status_code == 308
    assert '/api/calc/belt/vbelt' in r.headers.get('Location', '')


def test_legacy_calculate_get_redirects(client):
    r = client.get('/api/calculate/belt/vbelt', follow_redirects=False)
    assert r.status_code == 308
    assert '/api/calc/belt/vbelt' in r.headers.get('Location', '')


def test_legacy_material_search_redirects(client):
    r = client.get('/api/material/search?q=steel', follow_redirects=False)
    assert r.status_code == 308
    assert '/api/data/materials?q=steel' in r.headers.get('Location', '')


def test_legacy_material_info_redirects(client):
    r = client.get('/api/material/info?name=Q235', follow_redirects=False)
    assert r.status_code == 308
    assert '/api/data/materials/Q235' in r.headers.get('Location', '')


def test_legacy_fit_recommendations_implemented(client):
    """Phase 2 升级: /api/data/fit_recommendations 已由 p2_reference 蓝图实现"""
    r = client.get('/api/data/fit_recommendations')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    data = j['data']
    assert data['total'] >= 10
    assert len(data['items']) == data['total']
    # compat 层不再命中 (p2_reference 优先注册)


def test_legacy_motor_knowledge_implemented(client):
    """Phase 2 升级: /api/data/motor_knowledge 已由 p2_reference 蓝图实现"""
    r = client.get('/api/data/motor_knowledge')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    data = j['data']
    assert data['total'] >= 20
    assert len(data['items']) == data['total']
