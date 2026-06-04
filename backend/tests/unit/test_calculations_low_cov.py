"""单元测试: calculations/press.py / spring.py / surface.py / pneumatic.py / coupling.py

目标: 把整体覆盖率从 64% 提升到 ≥80%
"""
import math
import pytest
from backend.calculations.press import (
    blanking_force, stripping_force, v_bending_force, u_bending_force,
    embossing_force, shear_force,
)
from backend.calculations.spring import (
    coil_spring_compression, coil_spring_tension,
    coil_spring_stress, spring_deflection,
)
from backend.calculations.surface import (
    calc_roughness_convert, calc_hardness_convert, calc_surface_texture,
)
from backend.calculations.pneumatic import (
    calc_cylinder_force, calc_cylinder_air_consumption, calc_air_receiver_volume,
)
from backend.calculations.coupling import (
    coupling_gear_torque, coupling_universal, oring_groove,
    htd_synchronous_belt, motor_sync_speed, motor_torque, motor_current_estimate,
)


# ==================== press.py ====================

def test_blanking_force():
    r = blanking_force(perimeter_mm=100, thickness_mm=2, shear_strength_mpa=300)
    # F = 1.3·100·2·300/1000 = 78 kN
    assert r['blanking_force_kN'] == pytest.approx(78, rel=1e-3)


def test_blanking_force_custom_k():
    r = blanking_force(perimeter_mm=100, thickness_mm=2, shear_strength_mpa=300, k=1.5)
    assert r['blanking_force_kN'] == 90


def test_stripping_force_steel():
    r = stripping_force(blanking_force_kN=100, material_type='steel')
    assert r['material'] == 'steel'
    assert r['stripping_force_kN'] == 4
    assert r['ejecting_force_kN'] == 5
    assert r['pushing_force_kN'] == 6


def test_stripping_force_aluminum():
    r = stripping_force(blanking_force_kN=100, material_type='aluminum')
    assert r['stripping_force_kN'] == 6


def test_stripping_force_copper():
    r = stripping_force(blanking_force_kN=100, material_type='copper')
    assert r['material'] == 'copper'


def test_stripping_force_unknown_material():
    """未知材料 → 函数仍返回 'material' 字段, 系数兜底为 steel (4%)"""
    r = stripping_force(blanking_force_kN=100, material_type='xx_xxx')
    assert 'material' in r
    assert r['stripping_force_kN'] == 4  # 兜底为 steel 系数


def test_v_bending_force():
    r = v_bending_force(width_mm=50, thickness_mm=2, tensile_strength_mpa=400, die_opening_mm=10)
    # F = 1.33·50·4·400/(10·1000) = 10.64
    assert r['bending_type'] == 'V型弯曲'
    assert r['bending_force_kN'] == pytest.approx(10.64, rel=1e-2)


def test_u_bending_force():
    r = u_bending_force(width_mm=50, thickness_mm=2, tensile_strength_mpa=400, die_opening_mm=10)
    assert r['bending_type'] == 'U型弯曲'
    # U = 2*V
    assert r['bending_force_kN'] == pytest.approx(2 * 10.64, rel=1e-2)


def test_embossing_force():
    r = embossing_force(area_mm2=100, tensile_strength_mpa=400)
    # F = 100·400/1000 = 40
    assert r['embossing_force_kN'] == 40


def test_shear_force():
    r = shear_force(area_mm2=100, shear_strength_mpa=300)
    # F = 100·300/1000 = 30
    assert r['shear_force_kN'] == 30


# ==================== spring.py ====================

def test_coil_spring_compression():
    r = coil_spring_compression(d=4, Dm=30, n=10, G=79000, material='弹簧钢')
    assert r['spring_index'] == pytest.approx(30/4, rel=1e-3)
    assert r['stiffness_n_per_mm'] > 0
    assert r['material'] == '弹簧钢'


def test_coil_spring_compression_stainless():
    r = coil_spring_compression(d=4, Dm=30, n=10, material='不锈钢')
    # 不锈钢 G=73000
    assert r['shear_modulus'] == 73000


def test_coil_spring_compression_copper():
    r = coil_spring_compression(d=4, Dm=30, n=10, material='铜合金')
    assert r['shear_modulus'] == 45000


def test_coil_spring_tension():
    r = coil_spring_tension(d=4, Dm=30, n=10, F0=50, G=79000)
    assert r['stiffness_n_per_mm'] > 0
    assert r['initial_tension_n'] == 50


def test_coil_spring_stress():
    r = coil_spring_stress(d=4, Dm=30, F=100, material='弹簧钢')
    # tau = 8·K·F·Dm/(πd³)
    assert r['max_shear_stress_mpa'] > 0
    assert r['allowable_stress_mpa'] == 640
    assert r['is_safe'] is True


def test_coil_spring_stress_unsafe():
    """过大载荷 → 不安全"""
    r = coil_spring_stress(d=2, Dm=10, F=10000, material='弹簧钢')
    assert r['is_safe'] is False


def test_coil_spring_stress_unknown_material():
    """未知材料 → 兜底用弹簧钢"""
    r = coil_spring_stress(d=4, Dm=30, F=100, material='unknown_xx')
    assert r['allowable_stress_mpa'] == 640


def test_spring_deflection():
    r = spring_deflection(k=10, F=100)
    assert r['deflection_mm'] == 10


def test_spring_deflection_invalid_k():
    r = spring_deflection(k=0, F=100)
    assert 'error' in r


# ==================== surface.py ====================

def test_calc_roughness_convert():
    r = calc_roughness_convert(Ra=1.6)
    assert r['Ra_um'] == 1.6
    assert r['Rz_um'] > 0


def test_calc_roughness_convert_zero():
    r = calc_roughness_convert(Ra=0)
    # Ra=0 → Rz=0
    assert r['Rz_um'] == 0


def test_calc_hardness_convert():
    r = calc_hardness_convert(value=200, from_type='HB', to_type='HRC')
    # HB 200 → HRC 约 13
    assert isinstance(r, dict)


def test_calc_hardness_convert_to_same_type():
    r = calc_hardness_convert(value=200, from_type='HB', to_type='HB')
    assert isinstance(r, dict)


def test_calc_surface_texture():
    r = calc_surface_texture(Ra=0.8, process='turning')
    assert isinstance(r, dict)


def test_calc_surface_texture_no_process():
    r = calc_surface_texture(Ra=1.6)
    assert isinstance(r, dict)


# ==================== pneumatic.py ====================

def test_cylinder_force_extend():
    r = calc_cylinder_force(D=80, p=0.6, action_type='extend')
    # A = π·80²/4 ≈ 5026.55, F_theory = 5026.55·0.6 ≈ 3015.93
    assert r['effective_area_mm2'] == pytest.approx(5026.55, rel=1e-2)
    assert r['F_theory_N'] == pytest.approx(3015.93, rel=1e-2)


def test_cylinder_force_retract():
    r = calc_cylinder_force(D=80, d_rod=30, p=0.6, action_type='retract')
    # A = π(80²-30²)/4 ≈ 4320.13
    assert r['effective_area_mm2'] == pytest.approx(4320.13, rel=1e-2)


def test_cylinder_force_extend_with_rod():
    """extend + 有杆 → A 仍是无杆腔面积"""
    r = calc_cylinder_force(D=80, d_rod=30, p=0.6, action_type='extend')
    assert r['effective_area_mm2'] == pytest.approx(5026.55, rel=1e-2)


def test_cylinder_force_missing_D():
    r = calc_cylinder_force(D=0, p=0.6)
    assert 'error' in r


def test_cylinder_force_missing_p():
    r = calc_cylinder_force(D=80, p=0)
    assert 'error' in r


def test_cylinder_air_consumption_double():
    r = calc_cylinder_air_consumption(D=80, stroke=100, p=0.6, n_cycle=10, action_type='double')
    assert 'Q_L_min_ANR' in r
    # V_stroke = π·80²/4·100 = 502655 mm³ = 0.5027 L
    # V_stroke_ANR = 0.5027·(0.7013/0.1013) ≈ 3.479
    # Q = 3.479·10·2 = 69.59
    assert r['Q_L_min_ANR'] == pytest.approx(69.59, rel=1e-2)


def test_cylinder_air_consumption_single():
    r = calc_cylinder_air_consumption(D=80, stroke=100, p=0.6, n_cycle=10, action_type='single')
    # 单作用 n_eff=1
    assert r['Q_L_min_ANR'] == pytest.approx(34.79, rel=1e-2)


def test_cylinder_air_consumption_missing():
    r = calc_cylinder_air_consumption(D=0, stroke=100, p=0.6, n_cycle=10)
    assert 'error' in r


def test_air_receiver_volume():
    r = calc_air_receiver_volume(Q=1.0, p_max=0.8, p_min=0.6, t_cycle=1.0)
    # V = 1·1·0.1013/0.2 = 0.5065
    # 推荐 V = 0.5065*1.2 = 0.6078
    assert r['theoretical_volume_m3'] == pytest.approx(0.5065, rel=1e-2)
    assert r['recommended_volume_m3'] == pytest.approx(0.6078, rel=1e-2)


def test_air_receiver_volume_max_eq_min():
    """p_max == p_min → 错误"""
    r = calc_air_receiver_volume(Q=1.0, p_max=0.6, p_min=0.6, t_cycle=1.0)
    assert 'error' in r


def test_air_receiver_volume_missing():
    r = calc_air_receiver_volume(Q=0, p_max=0.8, p_min=0.6, t_cycle=1.0)
    assert 'error' in r


# ==================== coupling.py ====================

def test_coupling_gear_torque():
    r = coupling_gear_torque(power_kw=5, rpm=1450)
    # T = 9550·5/1450 ≈ 32.93
    assert r['actual_torque_nm'] == pytest.approx(32.93, rel=1e-2)
    # 选定 CL1, 710 N·m
    assert r['recommended_model'] in ['CL1', 'CL2', 'CL3']


def test_coupling_gear_torque_high_power():
    """大功率 → 推荐更大型号"""
    r = coupling_gear_torque(power_kw=100, rpm=1450, safety=2.0)
    # T_calc = 9550·100/1450·2 ≈ 1317
    assert r['actual_torque_nm'] > 500


def test_coupling_gear_torque_out_of_range():
    """超大 → 超出标准"""
    r = coupling_gear_torque(power_kw=10000, rpm=1450)
    assert r['is_safe'] is False
    assert '定制' in r['recommended_model']


def test_coupling_universal():
    r = coupling_universal(power_kw=5, rpm=1450, angle_deg=10)
    assert 'equivalent_torque_nm' in r
    assert 'efficiency' in r
    assert r['efficiency'] > 0.85


def test_coupling_universal_large_angle():
    r = coupling_universal(power_kw=5, rpm=1450, angle_deg=20)
    # 大角度效率更低
    assert r['efficiency'] <= 1.0


def test_oring_groove_standard():
    """标准截面 → 查表"""
    r = oring_groove(section_diam_mm=3.0)
    assert r['groove_depth_mm'] == 2.3
    assert r['groove_width_mm'] == 4.0


def test_oring_groove_nonstandard():
    """非标准 → 近似"""
    r = oring_groove(section_diam_mm=10.0)
    assert r['groove_depth_mm'] == 7.5  # 10 * 0.75
    assert r['groove_width_mm'] == 14.0  # 10 * 1.4


def test_htd_synchronous_belt_3m():
    r = htd_synchronous_belt(belt_type='3M', power_kw=1, n1_rpm=1450, ratio=2)
    assert r['pitch_mm'] == 3
    assert r['belt_type'] == '3M'


def test_htd_synchronous_belt_5m():
    r = htd_synchronous_belt(belt_type='5M', power_kw=2, n1_rpm=1450, ratio=3)
    assert r['pitch_mm'] == 5


def test_htd_synchronous_belt_with_teeth():
    r = htd_synchronous_belt(belt_type='8M', power_kw=5, n1_rpm=1450, ratio=2,
                             z1=24, width_mm=20)
    assert r['small_pulley_teeth'] == 24


def test_htd_synchronous_belt_unknown():
    r = htd_synchronous_belt(belt_type='XX-XXX', power_kw=5, n1_rpm=1450, ratio=2)
    assert 'error' in r


def test_motor_sync_speed_4p_50hz():
    r = motor_sync_speed(poles=4, freq=50)
    # n = 60·50/2 = 1500
    assert r['sync_speed_rpm'] == 1500


def test_motor_sync_speed_2p_50hz():
    r = motor_sync_speed(poles=2, freq=50)
    assert r['sync_speed_rpm'] == 3000


def test_motor_sync_speed_6p_60hz():
    r = motor_sync_speed(poles=6, freq=60)
    assert r['sync_speed_rpm'] == 1200


def test_motor_torque_with_rpm():
    r = motor_torque(power_kw=5, rpm=1450)
    # T = 9550·5/1450 ≈ 32.93
    assert r['torque_nm'] == pytest.approx(32.93, rel=1e-2)


def test_motor_torque_with_poles():
    """用极对数算同步转速, 再 *0.97"""
    r = motor_torque(power_kw=5, poles=4, freq=50)
    # rpm = 1500*0.97 = 1455
    assert r['torque_nm'] > 30
    assert r['speed_rpm'] == 1455


def test_motor_current_estimate_380v():
    r = motor_current_estimate(power_kw=11, voltage=380)
    # I = 11*2 = 22
    assert r['estimated_current_a'] == 22


def test_motor_current_estimate_220v():
    r = motor_current_estimate(power_kw=11, voltage=220)
    # I = 11*4.5 = 49.5
    assert r['estimated_current_a'] == 49.5
