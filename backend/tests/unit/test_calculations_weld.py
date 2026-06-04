"""单元测试: calculations/weld.py

目标覆盖率: ≥90%
"""
import pytest
from backend.calculations.weld import (
    calc_fillet_weld_stress, calc_butt_weld_stress,
)


# ============ calc_fillet_weld_stress: tension / shear ============

def test_fillet_weld_tension():
    """角焊缝受拉/受剪 (tension)"""
    r = calc_fillet_weld_stress(F=10000, h=10, Lw=100, load_type='tension')
    # throat = 0.707·10 = 7.07
    # A = 7.07·100 = 707
    # τ = 10000/707 ≈ 14.14
    assert r['throat_thickness_mm'] == pytest.approx(7.07, rel=1e-2)
    assert r['effective_area_mm2'] == pytest.approx(707, rel=1e-2)
    assert r['shear_stress_tau_MPa'] == pytest.approx(14.14, rel=1e-2)
    assert r['load_type'] == 'tension'


def test_fillet_weld_shear():
    r = calc_fillet_weld_stress(F=10000, h=10, Lw=100, load_type='shear')
    assert r['shear_stress_tau_MPa'] == pytest.approx(14.14, rel=1e-2)
    assert r['load_type'] == 'shear'


def test_fillet_weld_no_load():
    """受拉模式缺 F"""
    r = calc_fillet_weld_stress(F=None, h=10, Lw=100, load_type='tension')
    assert 'error' in r


def test_fillet_weld_missing_h():
    """缺 h"""
    r = calc_fillet_weld_stress(F=1000, h=0, Lw=100, load_type='tension')
    assert 'error' in r


def test_fillet_weld_missing_lw():
    """缺 Lw"""
    r = calc_fillet_weld_stress(F=1000, h=10, Lw=0, load_type='tension')
    assert 'error' in r


# ============ calc_fillet_weld_stress: combined (弯扭) ============

def test_fillet_weld_combined():
    """弯扭组合"""
    r = calc_fillet_weld_stress(F=5000, M=1e6, h=10, Lw=100, load_type='combined')
    # sigma_F = 5000/707 ≈ 7.07
    # W = 7.07·100²/6 ≈ 11783
    # sigma_M = 1e6/11783 ≈ 84.85
    # sigma_combined = √(7.07² + 84.85²) ≈ 85.15
    assert r['sigma_F_MPa'] == pytest.approx(7.07, rel=1e-2)
    assert r['sigma_M_MPa'] == pytest.approx(84.85, rel=1e-2)
    assert r['sigma_combined_MPa'] == pytest.approx(85.15, rel=1e-2)
    assert r['load_type'] == 'combined'


def test_fillet_weld_combined_missing_params():
    """组合模式缺 F/M"""
    r1 = calc_fillet_weld_stress(F=None, M=100, h=10, Lw=100, load_type='combined')
    r2 = calc_fillet_weld_stress(F=100, M=None, h=10, Lw=100, load_type='combined')
    assert 'error' in r1
    assert 'error' in r2


# ============ calc_butt_weld_stress: tension ============

def test_butt_weld_tension():
    r = calc_butt_weld_stress(F=20000, t=5, Lw=100, load_type='tension')
    assert r['effective_area_mm2'] == 500
    assert r['sigma_MPa'] == 40
    assert r['load_type'] == 'tension'


def test_butt_weld_tension_no_F():
    r = calc_butt_weld_stress(F=None, t=5, Lw=100, load_type='tension')
    assert 'error' in r


# ============ calc_butt_weld_stress: bending ============

def test_butt_weld_bending():
    """受弯 σ = 6M/(t·Lw²)"""
    r = calc_butt_weld_stress(M=1e6, t=10, Lw=100, load_type='bending')
    # W = 10·100²/6 ≈ 16667
    # σ = 1e6/16667 ≈ 60
    assert r['sigma_MPa'] == pytest.approx(60, rel=1e-2)
    assert r['load_type'] == 'bending'


def test_butt_weld_bending_no_M():
    r = calc_butt_weld_stress(M=None, t=10, Lw=100, load_type='bending')
    assert 'error' in r


# ============ calc_butt_weld_stress: combined (拉弯) ============

def test_butt_weld_combined():
    """拉弯组合"""
    r = calc_butt_weld_stress(F=20000, M=5e5, t=5, Lw=100, load_type='combined')
    # sigma_F = 20000/500 = 40
    # sigma_M = 5e5/416.67 ≈ 1200
    # 修正: W = 5·100²/6 ≈ 8333
    # sigma_M = 5e5/8333 ≈ 60
    # sigma_total = 40 + 60 = 100
    assert r['sigma_F_MPa'] == 40
    assert r['sigma_M_MPa'] == pytest.approx(60, rel=1e-2)
    assert r['sigma_total_MPa'] == pytest.approx(100, rel=1e-2)
    assert r['load_type'] == 'combined'


def test_butt_weld_combined_missing():
    r1 = calc_butt_weld_stress(F=None, M=100, t=5, Lw=100, load_type='combined')
    r2 = calc_butt_weld_stress(F=100, M=None, t=5, Lw=100, load_type='combined')
    assert 'error' in r1
    assert 'error' in r2


# ============ 缺参数边界 ============

def test_butt_weld_missing_t():
    r = calc_butt_weld_stress(F=100, t=0, Lw=100, load_type='tension')
    assert 'error' in r


def test_butt_weld_missing_lw():
    r = calc_butt_weld_stress(F=100, t=5, Lw=0, load_type='tension')
    assert 'error' in r
