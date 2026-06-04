"""单元测试: calculations/beam.py

目标覆盖率: ≥90%

注意: 函数返回键为 I_mm4, W_mm3 (无 area); 部分载荷类型未完全支持
(例如 simply_supported 的全段均布载荷公式在 L**3-2Lc²+c³=0 时返回 0,
 fixed_both 无 moment 处理器). 测试反映实际行为.
"""
import pytest
from backend.calculations.beam import (
    beam_section_inertia, calc_beam,
)


# ============ beam_section_inertia ============

def test_section_circle():
    r = beam_section_inertia('circle', d=100)
    assert r['I_mm4'] == pytest.approx(4908738.5, rel=1e-3)
    assert r['W_mm3'] == pytest.approx(98174.77, rel=1e-3)


def test_section_hollow_circle():
    r = beam_section_inertia('hollow_circle', D=100, d=50)
    assert r['I_mm4'] > 0
    assert r['W_mm3'] > 0


def test_section_rect():
    r = beam_section_inertia('rect', b=50, h=100)
    assert r['I_mm4'] == pytest.approx(50 * 100**3 / 12, rel=1e-3)
    assert r['W_mm3'] == pytest.approx(50 * 100**2 / 6, rel=1e-3)


def test_section_hollow_rect():
    r = beam_section_inertia('hollow_rect', B=100, H=50, b=60, h=30)
    assert r['I_mm4'] == pytest.approx((100 * 50**3 - 60 * 30**3) / 12, rel=1e-3)
    assert r['W_mm3'] > 0


def test_section_i_beam():
    r = beam_section_inertia('i_beam', B=100, H=200, t=10, tw=6)
    assert r['I_mm4'] > 0
    assert r['W_mm3'] > 0


def test_section_i_beam_no_tw():
    """不传 tw 时用 t 兜底"""
    r = beam_section_inertia('i_beam', B=100, H=200, t=10)
    assert r['I_mm4'] > 0


def test_section_channel():
    r = beam_section_inertia('channel', B=80, H=200, t=10, tw=5)
    assert r['I_mm4'] > 0
    assert r['W_mm3'] > 0
    assert 'centroid_x_mm' in r


def test_section_unknown():
    r = beam_section_inertia('unknown_xxx', x=1)
    assert 'error' in r


# ============ calc_beam: simply_supported ============

def test_simply_supported_point_load_center():
    """简支梁中点集中力 P=10kN, L=1000mm, a=500"""
    r = calc_beam('simply_supported', L=1000, loads=[
        {'type': 'point', 'F': 10000, 'a': 500},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] == pytest.approx(2500000, rel=1e-3)  # PL/4
    assert r['V_max_N'] == pytest.approx(5000, rel=1e-3)  # P/2
    assert r['delta_max_mm'] > 0


def test_simply_supported_point_offcenter():
    r = calc_beam('simply_supported', L=2000, loads=[
        {'type': 'point', 'F': 1000, 'a': 600},
    ], E=200000, I=5000000)
    assert r['M_max_N_mm'] > 0
    assert r['V_max_N'] > 0


def test_simply_supported_point_large_M():
    """a 接近 L → Ra 接近 F, M_x = Rb·b"""
    r = calc_beam('simply_supported', L=1000, loads=[
        {'type': 'point', 'F': 1000, 'a': 800},
    ], E=200000, I=1000000)
    # b=200, a=800 → M_max at a (M=Ra*a = 200*800=160000)
    assert r['M_max_N_mm'] == pytest.approx(160000, rel=1e-3)


def test_simply_supported_uniform_load():
    """非全长均布"""
    r = calc_beam('simply_supported', L=2000, loads=[
        {'type': 'uniform', 'q': 1, 'a': 0, 'b': 1000},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] > 0
    assert r['V_max_N'] > 0
    # 该实现公式 L**3-2Lc²+c³ 在 c=L 时为 0
    # 这里 c=1000, L=2000, c²=L², 结果可能非 0
    assert r['delta_max_mm'] >= 0


def test_simply_supported_moment_load():
    r = calc_beam('simply_supported', L=2000, loads=[
        {'type': 'moment', 'M': 5000, 'a': 800},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] >= 0
    assert 'load_details' in r


def test_simply_supported_unknown_load_type():
    """未知载荷类型 → 跳过, M_max 保持 0"""
    r = calc_beam('simply_supported', L=1000, loads=[
        {'type': 'unknown_xxx', 'F': 1, 'a': 1},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] == 0
    assert r['load_details'] == []


# ============ calc_beam: cantilever ============

def test_cantilever_point_load_tip():
    """悬臂梁自由端集中力 P=10N, L=500, a=500 (自由端)"""
    r = calc_beam('cantilever', L=500, loads=[
        {'type': 'point', 'F': 10, 'a': 500},
    ], E=200000, I=1000000)
    # M_fixed = F·a = 10*500 = 5000 N·mm
    assert r['M_max_N_mm'] == 5000
    assert r['V_max_N'] == 10
    assert r['delta_max_mm'] > 0


def test_cantilever_point_load_mid():
    """a < L 集中力"""
    r = calc_beam('cantilever', L=500, loads=[
        {'type': 'point', 'F': 10, 'a': 200},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] == 2000


def test_cantilever_uniform_load():
    r = calc_beam('cantilever', L=1000, loads=[
        {'type': 'uniform', 'q': 1, 'a': 0, 'b': 1000},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] > 0


def test_cantilever_moment_load():
    r = calc_beam('cantilever', L=500, loads=[
        {'type': 'moment', 'M': 100, 'a': 100},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] == 100
    assert r['delta_max_mm'] > 0


def test_cantilever_unknown_load_type():
    r = calc_beam('cantilever', L=1000, loads=[
        {'type': 'unknown', 'F': 1},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] == 0


# ============ calc_beam: fixed_both ============

def test_fixed_both_point_load_center():
    """两端固定梁中点集中力"""
    r = calc_beam('fixed_both', L=2000, loads=[
        {'type': 'point', 'F': 1000, 'a': 1000},
    ], E=200000, I=1000000)
    # M_A = M_B = P·a·b²/L² = 1000*1000*1000²/2000² = 250000
    assert r['M_max_N_mm'] == pytest.approx(250000, rel=1e-3)
    assert r['V_max_N'] == 1000


def test_fixed_both_point_load_offcenter():
    r = calc_beam('fixed_both', L=2000, loads=[
        {'type': 'point', 'F': 1000, 'a': 500},
    ], E=200000, I=1000000)
    # a=500, b=1500, M_A = P·a·b²/L² = 1000*500*1500²/2000² = 281250
    # M_B = P·a²·b/L² = 1000*500²*1500/2000² = 46875
    # M_max = 281250
    assert r['M_max_N_mm'] == pytest.approx(281250, rel=1e-3)


def test_fixed_both_uniform_load():
    r = calc_beam('fixed_both', L=2000, loads=[
        {'type': 'uniform', 'q': 1, 'a': 0, 'b': 2000},
    ], E=200000, I=1000000)
    # 端弯矩 qL²/12, 跨中 qL²/24
    assert r['M_max_N_mm'] == pytest.approx(2000**2 / 12, rel=1e-3)
    assert r['delta_max_mm'] > 0


def test_fixed_both_moment_load_not_supported():
    """fixed_both 没有 moment 处理器 → M_max 保持 0, 但函数仍返回完整字典"""
    r = calc_beam('fixed_both', L=1000, loads=[
        {'type': 'moment', 'M': 100, 'a': 500},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] == 0
    assert 'beam_type' in r


def test_fixed_both_unknown_type():
    r = calc_beam('fixed_both', L=1000, loads=[
        {'type': 'xx_yyy', 'F': 1},
    ], E=200000, I=1000000)
    assert r['M_max_N_mm'] == 0


# ============ 边界条件 ============

def test_beam_missing_params():
    """缺参数 → error"""
    r = calc_beam('simply_supported', L=1000, loads=None, E=200000, I=1000000)
    assert 'error' in r


def test_beam_zero_L():
    """L=0 → 进入 if 块, 返回 error"""
    r = calc_beam('simply_supported', L=0, loads=[{}], E=200000, I=1000000)
    assert 'error' in r


def test_beam_unknown_type_returns_error():
    """未知梁类型 → error (不是字典结构)"""
    r = calc_beam('unknown_type_xx', L=1000, loads=[{}], E=200000, I=1000000)
    assert 'error' in r
    assert '未知梁类型' in r['error']


def test_beam_zero_ei_returns_error():
    """E=0 或 I=0 → 触发 if not E 检查, 返回 error (不是字典)"""
    r = calc_beam('simply_supported', L=1000, loads=[
        {'type': 'point', 'F': 1000, 'a': 500},
    ], E=0, I=1000000)
    assert 'error' in r


def test_beam_zero_ei_both_zero():
    """E=0 且 I=0 → error"""
    r = calc_beam('simply_supported', L=1000, loads=[
        {'type': 'point', 'F': 1000, 'a': 500},
    ], E=0, I=0)
    assert 'error' in r


def test_beam_return_keys():
    """返回字典键完整"""
    r = calc_beam('simply_supported', L=1000, loads=[
        {'type': 'point', 'F': 1000, 'a': 500},
    ], E=200000, I=1000000)
    for k in ['beam_type', 'length_mm', 'E_MPa', 'I_mm4', 'EI_N_mm2',
              'M_max_N_mm', 'V_max_N', 'delta_max_mm', 'theta_max_rad',
              'theta_max_deg', 'load_details', 'formula', 'reference']:
        assert k in r
