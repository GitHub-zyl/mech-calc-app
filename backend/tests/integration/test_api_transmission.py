"""传动类 API 集成测试"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()


# ---- 齿轮 ----

def test_gear_spur(client):
    r = client.post('/api/calc/gear/spur', json={'module': 3, 'teeth': 20})
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert j['data']['pitch_diameter'] == 60.0


def test_gear_spur_missing(client):
    r = client.post('/api/calc/gear/spur', json={'module': 3})
    assert r.status_code == 400


def test_gear_mesh(client):
    r = client.post('/api/calc/gear/mesh', json={'module': 3, 'teeth1': 20, 'teeth2': 60})
    assert r.status_code == 200


def test_gear_motor(client):
    r = client.post('/api/calc/gear/motor', json={'power_kw': 5.5, 'n1_rpm': 1450, 'ratio': 30})
    assert r.status_code == 200


def test_gear_rack(client):
    r = client.post('/api/calc/gear/rack', json={'module': 3, 'z_pinion': 20})
    assert r.status_code == 200


def test_gear_bending(client):
    r = client.post('/api/calc/gear/bending', json={'Ft_N': 1000, 'b_mm': 20, 'm_mm': 3})
    assert r.status_code == 200


def test_gear_contact(client):
    r = client.post('/api/calc/gear/contact', json={'Ft_N': 1000, 'b_mm': 20, 'd1_mm': 60, 'u': 3})
    assert r.status_code == 200


def test_gear_force(client):
    r = client.post('/api/calc/gear/force', json={'torque_Nm': 100, 'd_mm': 80})
    assert r.status_code == 200


def test_gear_planetary(client):
    r = client.post('/api/calc/gear/planetary', json={'z_sun': 20, 'z_ring': 100, 'z_planet': 4})
    assert r.status_code == 200


def test_gear_compound(client):
    r = client.post('/api/calc/gear/compound', json={'teeth_list': [[20,40],[20,60],[15,60]]})
    assert r.status_code == 200


# ---- 蜗杆 ----

def test_worm_geometry(client):
    r = client.post('/api/calc/worm/geometry', json={'m': 2, 'z1': 1, 'z2': 30, 'q': 10})
    assert r.status_code == 200
    j = r.get_json()
    assert 'center_distance_mm' in j['data'] or 'center_distance' in j['data']


def test_worm_efficiency(client):
    r = client.post('/api/calc/worm/efficiency', json={'gamma_deg': 5.71})
    assert r.status_code == 200


# ---- 带 ----

def test_belt_vbelt(client):
    r = client.post('/api/calc/belt/vbelt', json={
        'section': 'A', 'power_kw': 5.5, 'n1_rpm': 1450, 'ratio': 2, 'center_distance_mm': 500
    })
    assert r.status_code == 200


def test_belt_synchronous(client):
    r = client.post('/api/calc/belt/synchronous', json={
        'belt_type': 'XL', 'power_kw': 1.5, 'n1_rpm': 1000, 'ratio': 2
    })
    assert r.status_code == 200


# ---- 链 ----

def test_chain_sprocket(client):
    r = client.post('/api/calc/chain/sprocket', json={'pitch': 12.7, 'teeth': 17})
    assert r.status_code == 200


def test_chain_length(client):
    r = client.post('/api/calc/chain/length', json={'pitch': 12.7, 'teeth1': 17, 'teeth2': 25, 'center_distance': 500})
    assert r.status_code == 200


def test_chain_conveyor(client):
    r = client.post('/api/calc/chain/conveyor', json={'mass_kg': 100, 'speed_mps': 1.5, 'length_m': 10})
    assert r.status_code == 200


# ---- 凸轮 ----

def test_cam_profile(client):
    r = client.post('/api/calc/cam/profile', json={'rb': 30, 'h': 10, 'beta_deg': 90, 'motion_type': 'sine'})
    assert r.status_code == 200


def test_cam_analysis(client):
    r = client.post('/api/calc/cam/analysis', json={'beta_deg': 90, 'h': 10, 'motion_type': 'sine'})
    assert r.status_code == 200


def test_cam_indexer(client):
    r = client.post('/api/calc/cam/indexer', json={'load_torque_nm': 50, 'index_angle_deg': 60, 'dwell_angle_deg': 300})
    assert r.status_code == 200


def test_cam_divider(client):
    r = client.post('/api/calc/cam/divider', json={'pitch_angle_deg': 30, 'table_diameter_mm': 400, 'load_mass_kg': 50})
    assert r.status_code == 200
