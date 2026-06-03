"""数据 API 集成测试"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_categories_listing(client):
    r = client.get('/api/data/categories')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert 'materials' in j['data']
    assert 'bearings' in j['data']
    assert 'constants' in j['data']


def test_materials_search(client):
    r = client.get('/api/data/materials?q=Iron')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert isinstance(j['data'], list)
    # 至少应返回一些 Iron 开头的材料
    if j['data']:
        names = [m.get('name', '') for m in j['data']]
        assert any('Iron' in n for n in names)


def test_materials_detail(client):
    r = client.get('/api/data/materials/Iron')
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        j = r.get_json()
        assert j['data']['name'] == 'Iron'


def test_materials_with_limit(client):
    r = client.get('/api/data/materials?limit=5')
    j = r.get_json()
    assert len(j['data']) <= 5


def test_bearings_deep_groove(client):
    r = client.get('/api/data/bearings')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)


def test_bearings_with_inner_diameter(client):
    r = client.get('/api/data/bearings?d=10')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)


def test_steel_grades(client):
    r = client.get('/api/data/steel-grades')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)


def test_aluminum_grades(client):
    r = client.get('/api/data/aluminum-grades')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)


def test_plastics(client):
    r = client.get('/api/data/plastics')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)


def test_oring_groove(client):
    r = client.get('/api/data/oring-groove')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)


def test_oring_with_diameter(client):
    r = client.get('/api/data/oring-groove?diameter=2.0')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)


def test_threads_metric(client):
    r = client.get('/api/data/threads/metric')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)


def test_threads_imperial(client):
    r = client.get('/api/data/threads/imperial')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)


def test_constants(client):
    r = client.get('/api/data/constants')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], dict)
    assert 'meta' in j
    assert j['meta']['count'] > 0
