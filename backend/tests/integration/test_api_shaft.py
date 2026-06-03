"""轴系/轴承/梁/疲劳 API 集成测试"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()


# ---- 轴 ----

def test_shaft_torsion(client):
    r = client.post('/api/calc/shaft/torsion', json={'d': 50, 'P': 5.5, 'n': 1450})
    assert r.status_code == 200


def test_shaft_combined(client):
    r = client.post('/api/calc/shaft/combined', json={'d': 50, 'M': 200, 'T': 100, 'sigma_allow': 100})
    assert r.status_code == 200


def test_shaft_fatigue(client):
    r = client.post('/api/calc/shaft/fatigue', json={'d': 50, 'M': 200, 'T': 100, 'sigma_b': 600})
    assert r.status_code == 200


def test_shaft_critical_speed(client):
    r = client.post('/api/calc/shaft/critical-speed', json={'d': 50, 'L': 1000, 'm_shaft': 10, 'm_disk': 5})
    assert r.status_code == 200


# ---- 轴承 ----

def test_bearing_life(client):
    r = client.post('/api/calc/bearing/life', json={'C_kN': 25, 'P_kN': 5, 'n_rpm': 3000})
    assert r.status_code == 200
    j = r.get_json()
    # 验证返回有寿命字段
    assert any(k in j['data'] for k in ('L10_hours', 'life_hours', 'L10h', 'L10_h', 'life', 'L10_life_hours'))


def test_bearing_equivalent(client):
    r = client.post('/api/calc/bearing/equivalent', json={'Fr_kN': 10, 'Fa_kN': 5})
    assert r.status_code == 200


def test_bearing_static(client):
    r = client.post('/api/calc/bearing/static-check', json={'C0_kN': 30, 'P0_kN': 5})
    assert r.status_code == 200


# ---- 梁 ----

def test_beam_section(client):
    r = client.post('/api/calc/beam/section', json={'shape': 'rect', 'b': 50, 'h': 100})
    assert r.status_code == 200


def test_beam_calc(client):
    r = client.post('/api/calc/beam/calc', json={
        'beam_type': 'simply_supported',
        'L': 1000,
        'loads': [{'type': 'point', 'F': 1000, 'a': 500}],
        'E': 206000,
        'I': 1e5,
    })
    assert r.status_code == 200


# ---- 疲劳 ----

def test_fatigue_sn(client):
    r = client.post('/api/calc/fatigue/sn-curve', json={'S_ut': 600, 'N1': 1e3, 'N2': 1e6})
    assert r.status_code == 200


def test_fatigue_stress_conc(client):
    r = client.post('/api/calc/fatigue/stress-conc', json={'K_t': 2.5, 'q': 0.7})
    assert r.status_code == 200


def test_fatigue_miner(client):
    r = client.post('/api/calc/fatigue/miner', json={
        'stress_levels': [200, 300, 400],
        'cycles': [1e5, 5e4, 1e4],
        'S_ut': 600,
        'Se': 250,
    })
    assert r.status_code == 200
