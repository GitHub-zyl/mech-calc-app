"""齿轮单元测试 - 不改实现,只测现有函数"""
import pytest
from backend.calculations.gear import (
    spur_gear_params, spur_gear_mesh, gear_motor_selection, rack_and_pinion,
    gear_bending_strength, gear_contact_strength, gear_force,
)
from backend.calculations.mechanics import planetary_gear, compound_gear_train


def test_spur_gear_basic():
    """m=3, z=20 → 分度圆 60, 齿顶圆 66"""
    r = spur_gear_params(m=3, z=20)
    assert r['pitch_diameter'] == 60.0
    assert r['tip_diameter'] == 66.0
    assert r['module'] == 3
    assert r['teeth'] == 20


def test_spur_gear_with_modification():
    """变位系数不影响分度圆直径"""
    r = spur_gear_params(m=3, z=20, x=0.3)
    assert r['modification_coefficient'] == 0.3
    assert r['pitch_diameter'] == 60.0


def test_mesh_basic():
    """齿轮副: 中心距 = m*(z1+z2)/2"""
    r = spur_gear_mesh(m=3, z1=20, z2=60)
    assert r['gear1']['teeth'] == 20
    assert r['gear2']['teeth'] == 60
    assert abs(r['center_distance'] - 120.0) < 1e-6


def test_gear_motor_selection():
    r = gear_motor_selection(5.5, 1450, 30, 0.95)
    assert 'output_speed' in r or 'n_out' in r or 'speed' in str(r).lower()


def test_rack_basic():
    r = rack_and_pinion(3, 20, force_n=100, speed_mps=1)
    assert isinstance(r, dict)


def test_gear_force():
    r = gear_force(torque_Nm=100, d_mm=80, alpha_deg=20, beta_deg=0)
    assert isinstance(r, dict)
    assert 'tangential_N' in r
    # 期望 Ft = 2*100*1000/80 = 2500
    assert abs(r['tangential_N'] - 2500) < 1


def test_planetary():
    r = planetary_gear(z_sun=20, z_ring=100, z_planet=4)
    assert isinstance(r, dict)
    # 该函数返回 ratio_fixed_ring/sun/carrier 多种比率
    assert any(k.startswith('ratio_') for k in r.keys())


def test_compound():
    """复合轮系 2×3×4 = 24 总传动比"""
    r = compound_gear_train([(20, 40), (20, 60), (15, 60)])
    assert isinstance(r, dict)
    assert abs(r['total_ratio'] - 24.0) < 1e-6


def test_bending_strength():
    r = gear_bending_strength(Ft_N=1000, b_mm=20, m_mm=3)
    assert isinstance(r, dict)


def test_contact_strength():
    r = gear_contact_strength(Ft_N=1000, b_mm=20, d1_mm=60, u=3)
    assert isinstance(r, dict)
