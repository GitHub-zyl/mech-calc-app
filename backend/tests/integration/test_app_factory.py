"""应用工厂 + 元信息端点集成测试"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_health(client):
    r = client.get('/api/meta/health')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert j['data']['app'] == 'mech-design-calc'
    assert j['data']['status'] == 'running'


def test_version(client):
    r = client.get('/api/meta/version')
    assert r.status_code == 200
    j = r.get_json()
    assert 'version' in j['data']


def test_categories_returns_13(client):
    r = client.get('/api/meta/categories')
    assert r.status_code == 200
    j = r.get_json()
    cats = j['data']
    assert isinstance(cats, list)
    assert len(cats) == 13
    ids = {c['id'] for c in cats}
    assert 'transmission' in ids
    assert 'units' in ids
    assert 'shaft_system' in ids


def test_category_detail(client):
    r = client.get('/api/meta/category/transmission')
    assert r.status_code == 200
    j = r.get_json()
    assert j['data']['id'] == 'transmission'
    assert 'name_zh' in j['data']


def test_category_404(client):
    r = client.get('/api/meta/category/unknown')
    assert r.status_code == 404
    j = r.get_json()
    assert j['status'] == 'error'


def test_index_page(client):
    r = client.get('/')
    # index.html 存在 → 200, 不存在 → 404
    assert r.status_code in (200, 404)
