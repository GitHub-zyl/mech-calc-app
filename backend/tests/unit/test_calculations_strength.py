"""单元测试: calculations/strength.py

目标覆盖率: ≥80%
"""
import math
import pytest
from backend.calculations.strength import (
    section_properties, column_buckling, column_stability_check,
    weld_fillet_stress, weld_butt_stress, key_strength, pin_strength,
    interference_fit, press_fit_force, rivet_strength, adhesive_strength,
)


# ============ section_properties ============

def test_section_rect():
    r = section_properties('rect', {'b': 50, 'h': 100})
    assert r['area_mm2'] == 5000
    assert r['inertia_mm4'] == pytest.approx(50 * 100**3 / 12, rel=1e-3)


def test_section_circle():
    r = section_properties('circle', {'d': 100})
    assert r['area_mm2'] == pytest.approx(math.pi * 100**2 / 4, rel=1e-3)


def test_section_tube():
    r = section_properties('tube', {'D': 100, 'd': 50})
    assert r['area_mm2'] == pytest.approx(math.pi * (100**2 - 50**2) / 4, rel=1e-3)
    assert r['inertia_mm4'] > 0


def test_section_square_tube():
    r = section_properties('square_tube', {'B': 100, 'H': 100, 'b': 80, 'h': 80})
    assert r['area_mm2'] == 100 * 100 - 80 * 80
    assert r['inertia_mm4'] > 0


def test_section_i_beam():
    r = section_properties('i_beam', {'B': 100, 'H': 200, 't': 10, 'tw': 6})
    assert r['area_mm2'] > 0
    assert r['inertia_mm4'] > 0


def test_section_i_beam_default_tw():
    r = section_properties('i_beam', {'B': 100, 'H': 200, 't': 10})
    assert r['area_mm2'] > 0


def test_section_t_section():
    r = section_properties('t_section', {'B': 100, 'H': 200, 't': 10, 'tw': 6})
    assert r['area_mm2'] > 0
    assert r['section_modulus_mm3'] > 0


def test_section_unknown():
    r = section_properties('unknown_xx', {'x': 1})
    assert 'error' in r


# ============ column_buckling ============

def test_column_buckling_euler():
    """Euler 弹性屈曲"""
    r = column_buckling(
        E_mpa=200000, L_mm=2000, I_mm4=1e6, A_mm2=1000, mu=1.0, sigma_s_mpa=235
    )
    # Pcr = π²EI/(μL)² = π²·2e5·1e6/(1·2e3)² ≈ 493480 N
    assert r['euler_critical_force_N'] == pytest.approx(493480, rel=1e-3)
    assert '屈曲' in r['failure_mode']


def test_column_buckling_johnson():
    """短粗杆 - 弹塑性屈曲"""
    r = column_buckling(
        E_mpa=200000, L_mm=100, I_mm4=1e6, A_mm2=1000, mu=1.0, sigma_s_mpa=235
    )
    # lam 小于 lam_p → 弹塑性
    assert '弹塑性' in r['failure_mode']


def test_column_buckling_fixed_fixed():
    """两端固定 mu=0.5"""
    r = column_buckling(
        E_mpa=200000, L_mm=2000, I_mm4=1e6, A_mm2=1000, mu=0.5, sigma_s_mpa=235
    )
    assert r['euler_critical_force_N'] > 0


# ============ column_stability_check ============

def test_column_stability_check_safe():
    r = column_stability_check(
        F_N=10000, A_mm2=1000, E_mpa=200000, L_mm=2000,
        I_mm4=1e6, mu=1.0, sigma_s_mpa=235, safety=2.0
    )
    assert 'is_safe' in r
    assert r['stability_safety_factor'] > 0


def test_column_stability_check_unsafe():
    """F 大到失稳"""
    r = column_stability_check(
        F_N=1e9, A_mm2=1000, E_mpa=200000, L_mm=2000,
        I_mm4=1e6, mu=1.0, sigma_s_mpa=235, safety=2.0
    )
    assert r['is_safe'] is False


# ============ weld_fillet_stress ============

def test_weld_fillet_stress_basic():
    r = weld_fillet_stress(F_N=10000, weld_leg_mm=10, weld_length_mm=100, num_welds=2)
    # A = 0.707·10·100·2 = 1414 mm²
    # τ = 10000/1414 ≈ 7.07 MPa
    assert r['effective_area_mm2'] == pytest.approx(1414, rel=1e-3)
    assert r['shear_stress_mpa'] == pytest.approx(7.07, rel=1e-2)


def test_weld_fillet_stress_single():
    r = weld_fillet_stress(F_N=1000, weld_leg_mm=5, weld_length_mm=50, num_welds=1)
    # 0.707*5 = 3.535, 函数 round 到 2 位 (banker's rounding)
    assert r['throat_thickness_mm'] == pytest.approx(3.535, abs=0.01)


# ============ weld_butt_stress ============

def test_weld_butt_stress():
    r = weld_butt_stress(F_N=20000, plate_thickness_mm=5, weld_width_mm=100)
    assert r['effective_area_mm2'] == 500
    assert r['tensile_stress_mpa'] == 40


# ============ key_strength ============

def test_key_strength():
    r = key_strength(
        T_Nmm=100000, shaft_diameter_mm=50, key_width_mm=10,
        key_height_mm=8, key_length_mm=40
    )
    # τ = 2T/(d·b·l) = 2·1e5/(50·10·40) = 10 MPa
    assert r['shear_stress_mpa'] == 10
    # σp = 4T/(d·h·l) = 4·1e5/(50·8·40) = 25 MPa
    assert r['bearing_stress_mpa'] == 25


def test_key_strength_zero_dim():
    r = key_strength(
        T_Nmm=100000, shaft_diameter_mm=0, key_width_mm=10,
        key_height_mm=8, key_length_mm=40
    )
    assert r['shear_stress_mpa'] == 0
    assert r['bearing_stress_mpa'] == 0


# ============ pin_strength ============

def test_pin_strength():
    r = pin_strength(F_N=1000, pin_diameter_mm=10, num_pins=1)
    # A = π·10²/4 ≈ 78.54, τ = 1000/78.54 ≈ 12.73
    assert r['total_area_mm2'] == pytest.approx(78.54, rel=1e-2)
    assert r['shear_stress_mpa'] == pytest.approx(12.73, rel=1e-2)


def test_pin_strength_two_pins():
    r = pin_strength(F_N=1000, pin_diameter_mm=10, num_pins=2)
    # 双销面积翻倍
    assert r['total_area_mm2'] == pytest.approx(157.08, rel=1e-2)


# ============ interference_fit ============

def test_interference_fit_basic():
    r = interference_fit(
        shaft_diameter_mm=50, interference_um=50, hub_od_mm=100,
        length_mm=50
    )
    assert r['contact_pressure_mpa'] > 0
    assert r['transmittable_torque_Nm'] > 0
    assert r['temp_rise_for_assembly_C'] > 0


def test_interference_fit_no_length():
    r = interference_fit(
        shaft_diameter_mm=50, interference_um=50, hub_od_mm=100
    )
    # 没给 length → 扭矩=0
    assert r['transmittable_torque_Nm'] == 0


# ============ press_fit_force ============

def test_press_fit_force():
    r = press_fit_force(
        shaft_diameter_mm=50, interference_um=50, hub_od_mm=100,
        length_mm=50
    )
    assert r['press_force_N'] > 0
    assert r['press_force_ton'] > 0


# ============ rivet_strength ============

def test_rivet_strength():
    r = rivet_strength(F_N=10000, d_mm=8, t_min_mm=5, n=4, shear_planes=2)
    # As = 4·π·8²/4 = 201 mm²
    # τ = 10000·2/201 ≈ 99.5 MPa
    assert r['shear_stress_mpa'] > 0
    assert r['bearing_stress_mpa'] > 0


def test_rivet_strength_zero_area():
    r = rivet_strength(F_N=10000, d_mm=0, t_min_mm=5, n=4, shear_planes=2)
    assert r['shear_stress_mpa'] == 0


# ============ adhesive_strength ============

def test_adhesive_strength():
    r = adhesive_strength(F_N=1000, width_mm=20, length_mm=50)
    assert r['area_mm2'] == 1000
    assert r['stress_mpa'] == 1.0


def test_adhesive_strength_zero_area():
    r = adhesive_strength(F_N=1000, width_mm=0, length_mm=0)
    assert r['stress_mpa'] == 0
