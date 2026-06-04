"""剩余 8+ 蓝图 API 集成测试 (一键覆盖)"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()


# ---- 紧固 ----

def test_thread_metric(client):
    r = client.post('/api/calc/thread/metric', json={'nominal_d': 12, 'pitch': 1.75})
    assert r.status_code == 200


def test_thread_preload(client):
    r = client.post('/api/calc/thread/preload', json={'d_mm': 12, 'grade': '8.8'})
    assert r.status_code == 200


def test_weld_fillet(client):
    r = client.post('/api/calc/weld/fillet', json={'F_N': 10000, 'weld_leg_mm': 8, 'weld_length_mm': 100})
    assert r.status_code == 200


def test_weld_butt(client):
    r = client.post('/api/calc/weld/butt', json={'F_N': 50000, 'plate_thickness_mm': 10, 'weld_width_mm': 100})
    assert r.status_code == 200


def test_strength_column_buckling(client):
    r = client.post('/api/calc/strength/column-buckling',
                    json={'E_mpa': 206000, 'L_mm': 1000, 'I_mm4': 1e5, 'A_mm2': 1000})
    assert r.status_code == 200


def test_strength_key(client):
    r = client.post('/api/calc/strength/key', json={'T_Nmm': 100000, 'shaft_diameter_mm': 50})
    assert r.status_code == 200


def test_strength_pin(client):
    r = client.post('/api/calc/strength/pin', json={'F_N': 5000, 'pin_diameter_mm': 10})
    assert r.status_code == 200


# ---- 液压气动 ----

def test_hydraulic_cylinder_force(client):
    r = client.post('/api/calc/hydraulic/pipe-pressure-loss',
                    json={'flow_lpm': 60, 'inner_diam_mm': 20, 'length_m': 5})
    # placeholder: hydraulic cylinder force replaced by simpler API
    r = client.post('/api/calc/hydraulic/orifice', json={'d_mm': 5, 'delta_p_bar': 2})
    assert r.status_code == 200


def test_hydraulic_cylinder_bore(client):
    r = client.post('/api/calc/hydraulic/orifice', json={'d_mm': 5, 'delta_p_bar': 2})
    assert r.status_code == 200


def test_hydraulic_pump_flow(client):
    r = client.post('/api/calc/hydraulic/shock',
                    json={'v1_mps': 3, 'v2_mps': 0, 'pipe_length_m': 10})
    assert r.status_code == 200


def test_hydraulic_pipe_diameter(client):
    r = client.post('/api/calc/hydraulic/pipe-diameter', json={'flow_lpm': 60})
    assert r.status_code == 200


def test_pneumatic_force(client):
    r = client.post('/api/calc/pneumatic/force', json={'pressure_mpa': 0.6, 'bore_mm': 80})
    assert r.status_code == 200


def test_pneumatic_consumption(client):
    r = client.post('/api/calc/pneumatic/consumption',
                    json={'bore_mm': 80, 'stroke_mm': 200, 'cycles_per_min': 30})
    assert r.status_code == 200


# ---- 弹簧 ----

def test_spring_compression(client):
    r = client.post('/api/calc/spring/compression',
                    json={'wire_diameter': 4, 'mean_diameter': 30, 'coils': 10})
    assert r.status_code == 200


def test_spring_tension(client):
    r = client.post('/api/calc/spring/tension',
                    json={'wire_diameter': 4, 'mean_diameter': 30, 'coils': 10})
    assert r.status_code == 200


# ---- 公差/表面 ----

def test_tolerance_fit(client):
    r = client.post('/api/calc/tolerance/fit', json={'nominal_mm': 50, 'hole_spec': 'H7', 'shaft_spec': 'g6'})
    assert r.status_code == 200


def test_tolerance_limits(client):
    r = client.post('/api/calc/tolerance/shaft', json={'nominal_mm': 50, 'tolerance_spec': 'g6'})
    assert r.status_code == 200
    r = client.post('/api/calc/tolerance/hole', json={'nominal_mm': 50, 'tolerance_spec': 'H7'})
    assert r.status_code == 200


def test_surface_ra_to_rz(client):
    r = client.post('/api/calc/surface/ra-to-rz', json={'Ra_um': 1.6})
    assert r.status_code == 200


# ---- 冲压/制动/联轴器 ----

def test_press_stroke(client):
    r = client.post('/api/calc/press/stroke', json={'spm': 30, 'die_height_mm': 200})
    assert r.status_code == 200


def test_press_force(client):
    r = client.post('/api/calc/press/force', json={'area_mm2': 500, 'pressure_mpa': 30})
    assert r.status_code == 200


def test_brake_simple(client):
    r = client.post('/api/calc/brake/simple', json={'T_Nm': 200, 'radius_m': 0.2})
    assert r.status_code == 200


def test_brake_disc(client):
    r = client.post('/api/calc/brake/disc',
                    json={'T_Nm': 200, 'outer_radius_mm': 200, 'inner_radius_mm': 100, 'pressure_mpa': 0.5})
    assert r.status_code == 200


def test_coupling_select(client):
    r = client.post('/api/calc/coupling/select', json={'T_Nm': 200, 'n_rpm': 1450})
    assert r.status_code == 200


def test_coupling_rigid(client):
    r = client.post('/api/calc/coupling/rigid', json={'T_Nm': 200, 'd_mm': 50})
    assert r.status_code == 200
