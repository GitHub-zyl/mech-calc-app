"""P2 集成测试: /api/data/fit_recommendations + /api/data/motor_knowledge"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()


# ============ 配合度推荐 ============

def test_fit_recommendations_list_all(client):
    r = client.get('/api/data/fit_recommendations')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    data = j['data']
    assert data['total'] >= 10
    assert len(data['items']) == data['total']


def test_fit_recommendations_filter_by_fit_type(client):
    r = client.get('/api/data/fit_recommendations?fit_type=间隙')
    j = r.get_json()
    items = j['data']['items']
    assert all(it['fit_type'] == '间隙' for it in items)
    assert j['data']['filtered'] >= 3


def test_fit_recommendations_filter_by_category(client):
    r = client.get('/api/data/fit_recommendations?category=滑动')
    j = r.get_json()
    assert all(it['category'] == '滑动' for it in j['data']['items'])


def test_fit_recommendations_combined(client):
    r = client.get('/api/data/fit_recommendations?fit_type=间隙&category=滑动')
    j = r.get_json()
    items = j['data']['items']
    assert all(it['fit_type'] == '间隙' and it['category'] == '滑动' for it in items)


def test_fit_recommendations_meta_includes_types(client):
    r = client.get('/api/data/fit_recommendations')
    data = r.get_json()['data']
    assert '间隙' in data['fit_types']
    assert '过渡' in data['fit_types']
    assert '过盈' in data['fit_types']


def test_fit_recommendations_detail_success(client):
    r = client.get('/api/data/fit_recommendations/H7g6')
    assert r.status_code == 200
    j = r.get_json()
    assert j['data']['id'] == 'H7g6'
    assert j['data']['hole'] == 'H7'
    assert j['data']['shaft'] == 'g6'


def test_fit_recommendations_detail_not_found(client):
    r = client.get('/api/data/fit_recommendations/no_such_fit')
    assert r.status_code == 404


# ============ 电机常识 ============

def test_motor_knowledge_list_all(client):
    r = client.get('/api/data/motor_knowledge')
    assert r.status_code == 200
    j = r.get_json()
    data = j['data']
    assert data['total'] >= 20
    assert len(data['items']) == data['total']


def test_motor_knowledge_filter_by_category(client):
    r = client.get('/api/data/motor_knowledge?category=铭牌')
    j = r.get_json()
    assert all(it['category'] == '铭牌' for it in j['data']['items'])


def test_motor_knowledge_meta_includes_categories(client):
    r = client.get('/api/data/motor_knowledge')
    data = r.get_json()['data']
    assert '铭牌' in data['categories']
    assert '起动' in data['categories']


def test_motor_knowledge_detail_success(client):
    r = client.get('/api/data/motor_knowledge/motor_sync_speed_50hz_4p')
    assert r.status_code == 200
    j = r.get_json()
    assert j['data']['id'] == 'motor_sync_speed_50hz_4p'
    assert j['data']['value'] == 1500


def test_motor_knowledge_detail_not_found(client):
    r = client.get('/api/data/motor_knowledge/no_such_id')
    assert r.status_code == 404


# ============ 通用 ============

def test_response_shape(client):
    """所有响应符合统一格式"""
    for url in ['/api/data/fit_recommendations',
                '/api/data/fit_recommendations/H7g6',
                '/api/data/motor_knowledge',
                '/api/data/motor_knowledge/motor_sync_speed_50hz_4p']:
        r = client.get(url)
        j = r.get_json()
        assert j['status'] == 'ok'
        assert 'data' in j
