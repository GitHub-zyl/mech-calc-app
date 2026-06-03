"""单位换算 API 集成测试"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_categories_list(client):
    r = client.get('/api/units/categories')
    assert r.status_code == 200
    j = r.get_json()
    cats = j['data']
    assert isinstance(cats, list)
    ids = {c['id'] for c in cats}
    assert 'length' in ids
    assert 'pressure' in ids
    assert 'force' in ids
    for c in cats:
        assert 'units' in c
        assert isinstance(c['units'], list)
        assert c['units']


def test_category_detail(client):
    r = client.get('/api/units/category/length')
    assert r.status_code == 200
    j = r.get_json()
    assert j['data']['id'] == 'length'
    assert 'm' in j['data']['units'] or 'mm' in j['data']['units']


def test_category_404(client):
    r = client.get('/api/units/category/unknown')
    assert r.status_code == 404


def test_convert_length_m_to_mm(client):
    r = client.post('/api/units/convert', json={
        'value': 1, 'from': 'm', 'to': 'mm', 'category': 'length'
    })
    assert r.status_code == 200
    j = r.get_json()
    assert abs(j['data']['value'] - 1000) < 1e-6
    assert j['data']['from'] == 'm'
    assert j['data']['to'] == 'mm'


def test_convert_pressure_mpa_to_pa(client):
    r = client.post('/api/units/convert', json={
        'value': 1, 'from': 'MPa', 'to': 'Pa', 'category': 'pressure'
    })
    j = r.get_json()
    assert abs(j['data']['value'] - 1e6) < 1


def test_convert_force_kn_to_n(client):
    r = client.post('/api/units/convert', json={
        'value': 1, 'from': 'kN', 'to': 'N', 'category': 'force'
    })
    j = r.get_json()
    assert abs(j['data']['value'] - 1000) < 1e-6


def test_convert_torque(client):
    r = client.post('/api/units/convert', json={
        'value': 1, 'from': 'N·m', 'to': 'N·mm', 'category': 'torque'
    })
    j = r.get_json()
    assert abs(j['data']['value'] - 1000) < 1e-6


def test_convert_invalid_unit(client):
    r = client.post('/api/units/convert', json={
        'value': 1, 'from': 'xyz', 'to': 'mm', 'category': 'length'
    })
    assert r.status_code == 400
    j = r.get_json()
    assert j['status'] == 'error'


def test_convert_missing_value(client):
    r = client.post('/api/units/convert', json={
        'from': 'm', 'to': 'mm', 'category': 'length'
    })
    assert r.status_code == 400


def test_convert_missing_from(client):
    r = client.post('/api/units/convert', json={
        'value': 1, 'to': 'mm', 'category': 'length'
    })
    assert r.status_code == 400


def test_batch_convert(client):
    r = client.post('/api/units/convert/batch', json={
        'items': [
            {'value': 1, 'from': 'm', 'to': 'mm', 'category': 'length'},
            {'value': 1, 'from': 'MPa', 'to': 'Pa', 'category': 'pressure'},
            {'value': 100, 'from': 'mm', 'to': 'cm', 'category': 'length'},
        ]
    })
    j = r.get_json()
    assert j['status'] == 'ok'
    assert j['meta']['count'] == 3
    assert j['meta']['success'] == 3
    assert j['data'][0]['value'] == 1000
    assert abs(j['data'][1]['value'] - 1e6) < 1
    assert abs(j['data'][2]['value'] - 10) < 1e-6


def test_batch_empty(client):
    r = client.post('/api/units/convert/batch', json={'items': []})
    assert r.status_code == 400


def test_constants(client):
    r = client.get('/api/units/constants')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], dict)
    assert j['meta']['count'] > 0
