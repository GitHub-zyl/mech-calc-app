"""集成测试: /api/history REST 接口"""
import json
import pytest
from backend.app import create_app
from backend.database import clear_all


@pytest.fixture
def client():
    app = create_app(testing=True)
    # 清空测试库
    with app.app_context():
        clear_all()
    return app.test_client()


def test_health(client):
    """健康检查"""
    r = client.get('/api/history/stats')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'


# ============ POST ============

def test_post_history_success(client):
    body = {
        'category': 'gear',
        'endpoint': '/api/calc/gear/spur',
        'calc_id': 'gear-spur',
        'input': {'module': 2, 'teeth': 20},
        'output': {'d_pitch_mm': 40, 'da_mm': 44},
        'duration_ms': 1.5,
    }
    r = client.post('/api/history', json=body)
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert 'id' in j['data']
    assert j['data']['record']['category'] == 'gear'
    assert j['data']['record']['input']['module'] == 2


def test_post_missing_category(client):
    r = client.post('/api/history', json={
        'endpoint': '/x', 'input': {}, 'output': {}
    })
    assert r.status_code == 400
    j = r.get_json()
    assert j['status'] == 'error'


def test_post_missing_endpoint(client):
    r = client.post('/api/history', json={
        'category': 'x', 'input': {}, 'output': {}
    })
    assert r.status_code == 400


def test_post_missing_input(client):
    r = client.post('/api/history', json={
        'category': 'x', 'endpoint': '/x', 'output': {}
    })
    assert r.status_code == 400


def test_post_no_json(client):
    r = client.post('/api/history', data='not json', content_type='text/plain')
    assert r.status_code == 400


def test_post_empty_category(client):
    r = client.post('/api/history', json={
        'category': '   ', 'endpoint': '/x', 'input': {}, 'output': {}
    })
    assert r.status_code == 400


# ============ GET list ============

def test_get_list_empty(client):
    r = client.get('/api/history')
    assert r.status_code == 200
    j = r.get_json()
    assert j['data']['items'] == []
    assert j['data']['pagination']['total'] == 0


def test_get_list_with_records(client):
    for i in range(3):
        client.post('/api/history', json={
            'category': 'gear', 'endpoint': '/x',
            'input': {'i': i}, 'output': {}
        })
    r = client.get('/api/history')
    j = r.get_json()
    assert j['data']['pagination']['total'] == 3
    assert len(j['data']['items']) == 3


def test_get_list_pagination(client):
    for i in range(5):
        client.post('/api/history', json={
            'category': 'x', 'endpoint': '/x', 'input': {}, 'output': {}
        })
    r1 = client.get('/api/history?limit=2&offset=0')
    r2 = client.get('/api/history?limit=2&offset=2')
    assert r1.get_json()['data']['pagination']['has_more'] is True
    assert r2.get_json()['data']['pagination']['has_more'] is True
    r3 = client.get('/api/history?limit=2&offset=4')
    assert r3.get_json()['data']['pagination']['has_more'] is False


def test_get_list_limit_capped(client):
    """limit 最大 200"""
    r = client.get('/api/history?limit=99999')
    # 参数被规整到 200
    assert r.get_json()['data']['pagination']['limit'] == 200


def test_get_list_limit_invalid(client):
    r = client.get('/api/history?limit=abc')
    assert r.status_code == 400


def test_get_list_filter_by_category(client):
    client.post('/api/history', json={'category': 'gear', 'endpoint': '/x', 'input': {}, 'output': {}})
    client.post('/api/history', json={'category': 'bearing', 'endpoint': '/x', 'input': {}, 'output': {}})
    r = client.get('/api/history?category=gear')
    items = r.get_json()['data']['items']
    assert all(it['category'] == 'gear' for it in items)


# ============ GET detail ============

def test_get_detail_success(client):
    body = {'category': 'x', 'endpoint': '/x', 'input': {'a': 1}, 'output': {'b': 2}}
    post_r = client.post('/api/history', json=body)
    rid = post_r.get_json()['data']['id']
    r = client.get(f'/api/history/{rid}')
    assert r.status_code == 200
    j = r.get_json()
    assert j['data']['id'] == rid
    assert j['data']['input'] == {'a': 1}


def test_get_detail_not_found(client):
    r = client.get('/api/history/99999')
    assert r.status_code == 404


# ============ DELETE ============

def test_delete_single_success(client):
    rid = client.post('/api/history', json={
        'category': 'x', 'endpoint': '/x', 'input': {}, 'output': {}
    }).get_json()['data']['id']
    r = client.delete(f'/api/history/{rid}')
    assert r.status_code == 200
    assert r.get_json()['data']['deleted'] is True


def test_delete_single_not_found(client):
    r = client.delete('/api/history/99999')
    assert r.status_code == 404


def test_delete_batch(client):
    ids = [client.post('/api/history', json={
        'category': 'x', 'endpoint': '/x', 'input': {}, 'output': {}
    }).get_json()['data']['id'] for _ in range(3)]
    r = client.delete(f'/api/history?ids={",".join(str(i) for i in ids)}')
    j = r.get_json()
    assert j['data']['requested'] == 3
    assert j['data']['deleted'] == 3


def test_delete_batch_no_ids(client):
    r = client.delete('/api/history')
    assert r.status_code == 400


def test_delete_batch_invalid_ids(client):
    r = client.delete('/api/history?ids=1,abc,3')
    assert r.status_code == 400


def test_delete_all(client):
    for _ in range(3):
        client.post('/api/history', json={
            'category': 'x', 'endpoint': '/x', 'input': {}, 'output': {}
        })
    r = client.delete('/api/history?all=1')
    assert r.status_code == 200
    assert r.get_json()['data']['cleared'] == 3


# ============ stats ============

def test_stats(client):
    client.post('/api/history', json={'category': 'gear', 'endpoint': '/x', 'input': {}, 'output': {}})
    client.post('/api/history', json={'category': 'bearing', 'endpoint': '/x', 'input': {}, 'output': {}})
    r = client.get('/api/history/stats')
    j = r.get_json()
    assert j['data']['total'] == 2
    assert j['data']['by_category']['gear'] == 1
    assert j['data']['by_category']['bearing'] == 1


def test_categories(client):
    client.post('/api/history', json={'category': 'gear', 'endpoint': '/x', 'input': {}, 'output': {}})
    r = client.get('/api/history/categories')
    assert 'gear' in r.get_json()['data']


# ============ 边界 ============

def test_unicode_in_input_output(client):
    """中文 JSON 正确存取"""
    r = client.post('/api/history', json={
        'category': '材料', 'endpoint': '/x',
        'input': {'材料': 'Q235', '厚度': '2mm'},
        'output': {'结论': 'OK'},
    })
    assert r.status_code == 200
    rid = r.get_json()['data']['id']
    rec = client.get(f'/api/history/{rid}').get_json()['data']
    assert rec['input']['材料'] == 'Q235'
    assert rec['output']['结论'] == 'OK'


def test_nested_dict(client):
    """嵌套 dict 正确反序列化"""
    payload = {
        'category': 'x', 'endpoint': '/x',
        'input': {'a': {'b': {'c': [1, 2, 3]}}},
        'output': [{'k1': 'v1'}, {'k2': 'v2'}],
    }
    rid = client.post('/api/history', json=payload).get_json()['data']['id']
    rec = client.get(f'/api/history/{rid}').get_json()['data']
    assert rec['input'] == {'a': {'b': {'c': [1, 2, 3]}}}
    assert rec['output'] == [{'k1': 'v1'}, {'k2': 'v2'}]


def test_client_ip_header(client):
    """X-Forwarded-For 头被记录"""
    r = client.post('/api/history', json={
        'category': 'x', 'endpoint': '/x', 'input': {}, 'output': {}
    }, headers={'X-Forwarded-For': '203.0.113.42'})
    assert r.status_code == 200
    rid = r.get_json()['data']['id']
    rec = client.get(f'/api/history/{rid}').get_json()['data']
    assert rec['client_ip'] == '203.0.113.42'
