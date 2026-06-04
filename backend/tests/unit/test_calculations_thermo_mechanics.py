"""单元测试: calculations/thermo.py + calculations/mechanics.py

目标: 把覆盖率从 68% 提升到 ≥80%

注意: 函数键名以 calculations 实际返回值为准, 不臆造.
"""
import math
import pytest
from backend.calculations.thermo import (
    conduction, convection, thermal_expansion, thermal_stress,
    bernoulli, orifice_flow, pipe_velocity, weir_flow, ideal_gas,
)
from backend.calculations.mechanics import (
    linear_motion, rotational_motion, centrifugal_force,
    momentum, angular_momentum, impulse, work_energy, power_calc,
    friction, mass_inertia, parallel_axis_theorem, radius_of_gyration,
    spring_mass_vibration, torsional_vibration, critical_shaft_speed,
    simple_pendulum, flywheel_energy, brake_torque, lead_screw_efficiency,
    screw_jack_torque, planetary_gear, compound_gear_train,
)


# ==================== thermo.py ====================

# ----- 热传导 -----
def test_conduction_find_Q():
    """Q = k·A·ΔT/L"""
    r = conduction(k=50, A=0.1, dT=20, L=0.01)
    assert r['heat_flow_W'] == 10000


def test_conduction_find_k():
    r = conduction(Q=10000, A=0.1, dT=20, L=0.01)
    assert r['thermal_conductivity_W_mK'] == 50


def test_conduction_find_A():
    r = conduction(Q=10000, k=50, dT=20, L=0.01)
    assert r['area_m2'] == 0.1


def test_conduction_find_dT():
    r = conduction(Q=10000, k=50, A=0.1, L=0.01)
    assert r['temp_diff_K'] == 20


def test_conduction_find_L():
    r = conduction(Q=10000, k=50, A=0.1, dT=20)
    assert r['thickness_m'] == 0.01


def test_conduction_wrong_count():
    r = conduction(k=50, A=0.1, dT=20)
    assert 'error' in r


# ----- 热对流 -----
def test_convection_find_Q():
    r = convection(h=10, A=2, dT=15)
    assert r['heat_flow_W'] == 300


def test_convection_find_h():
    r = convection(Q=300, A=2, dT=15)
    assert r['heat_transfer_coeff_W_m2K'] == 10


def test_convection_find_A():
    r = convection(Q=300, h=10, dT=15)
    assert r['area_m2'] == 2


def test_convection_find_dT():
    r = convection(Q=300, h=10, A=2)
    assert r['temp_diff_K'] == 15


def test_convection_wrong_count():
    r = convection(h=10, A=2)
    assert 'error' in r


# ----- 热膨胀 / 热应力 -----
def test_thermal_expansion_steel():
    r = thermal_expansion(L0_m=1.0, dT_K=50, alpha=1.2e-5)
    # ΔL = 1.2e-5 * 1.0 * 50 = 6e-4 m = 0.6 mm
    assert r['expansion_mm'] == pytest.approx(0.6, abs=1e-4)


def test_thermal_expansion_default_alpha():
    r = thermal_expansion(L0_m=1.0, dT_K=100)
    assert r['expansion_coeff'] == 1.2e-5


def test_thermal_stress():
    r = thermal_stress(E_mpa=200000, dT_K=50)
    assert r['thermal_stress_mpa'] == 120


def test_thermal_stress_custom_alpha():
    r = thermal_stress(E_mpa=100000, dT_K=100, alpha=2.4e-5)
    assert r['thermal_stress_mpa'] == 240


# ----- 伯努利 -----
def test_bernoulli_find_v1():
    """反推 v1: p1=100kPa < p2=200kPa, v2=10, h1=h2=0
    0.5·1000·v1² = 200000-100000+0.5·1000·100 = 150000
    v1 = √300 ≈ 17.32"""
    r = bernoulli(p1=100000, p2=200000, v2=10, h1=0, h2=0)
    assert r['v1_mps'] == pytest.approx(17.32, rel=1e-2)


def test_bernoulli_find_v2():
    """反推 v2: 0.5·1000·v2² = 200000-100000+0.5·1000·0 = 100000 → v2≈14.14"""
    r = bernoulli(p1=200000, p2=100000, v1=0, h1=0, h2=0)
    assert r['v2_mps'] == pytest.approx(14.14, rel=1e-2)


def test_bernoulli_find_p1():
    """已知 p2, v1, v2, h1, h2 求 p1"""
    r = bernoulli(p2=100000, v1=10, v2=5, h1=0, h2=0)
    # p1 = 100000 + 0.5·1000·(25-100) = 100000 - 37500 = 62500
    assert r['p1_Pa'] == pytest.approx(62500, rel=1e-2)


def test_bernoulli_find_p2():
    """已知 p1, v1, v2, h1, h2 求 p2"""
    r = bernoulli(p1=100000, v1=10, v2=5, h1=0, h2=0)
    # p2 = 100000 + 0.5·1000·(100-25) = 100000 + 37500 = 137500
    assert r['p2_Pa'] == pytest.approx(137500, rel=1e-2)


def test_bernoulli_too_few_known():
    r = bernoulli(p1=100)
    assert 'error' in r


# ----- 孔板流量 -----
def test_orifice_flow():
    r = orifice_flow(d_mm=10, delta_p_Pa=1000, Cd=0.62)
    assert r['orifice_diameter_mm'] == 10
    assert r['flow_m3s'] > 0


# ----- 管流速度 -----
def test_pipe_velocity_m3s():
    r = pipe_velocity(Q_m3s=0.001, d_mm=50)
    assert r['velocity_mps'] == pytest.approx(0.509, rel=1e-2)


def test_pipe_velocity_lpm():
    r = pipe_velocity(Q_lpm=60, d_mm=50)
    assert r['velocity_mps'] > 0


def test_pipe_velocity_missing():
    r = pipe_velocity(d_mm=50)
    assert 'error' in r


# ----- 堰流 -----
def test_weir_flow():
    r = weir_flow(b_m=0.5, h_m=0.1)
    assert r['flow_m3s'] > 0


# ----- 理想气体 -----
def test_ideal_gas_with_moles():
    r = ideal_gas(p_Pa=101325, V_m3=0.0224, T_K=273.15, n_mol=1.0)
    assert r['pV_value'] > 0


def test_ideal_gas_with_mass():
    r = ideal_gas(p_Pa=101325, V_m3=0.0224, T_K=273.15, m_kg=0.029)
    assert r['moles'] == pytest.approx(1.0, rel=1e-2)


def test_ideal_gas_no_moles():
    r = ideal_gas(p_Pa=101325, V_m3=1, T_K=273.15)
    assert 'error' in r


# ==================== mechanics.py ====================

# ----- 直线运动 (key: s, v) -----
def test_linear_motion_find_s():
    r = linear_motion(v0=0, a=2, t=5)
    assert r['s'] == 25
    assert r['v'] == 10


def test_linear_motion_find_v():
    r = linear_motion(v0=0, a=2, t=5)
    assert r['v'] == 10


def test_linear_motion_given_s():
    """已知 v0, t, s → 函数无法反推 a (无对应分支), 返回默认 a=0"""
    r = linear_motion(v0=0, t=5, s=50)
    # 函数仅支持 v0+a+t 输入, 缺 a 时不主动求解
    assert r['a'] == 0
    assert r['t'] == 5
    assert r['s'] == 50


def test_linear_motion_all_given():
    """所有参数都给出 → 直接使用"""
    r = linear_motion(v0=2, a=3, t=4)
    # s = 2·4 + 0.5·3·16 = 8 + 24 = 32
    assert r['s'] == 32
    # v = 2 + 3·4 = 14
    assert r['v'] == 14


# ----- 旋转运动 (key: theta_rad) -----
def test_rotational_motion():
    r = rotational_motion(omega0=0, alpha=2, t=5)
    assert r['omega_rad_s'] == 10
    assert r['theta_rad'] == 25


# ----- 离心力 -----
def test_centrifugal_force_with_omega():
    r = centrifugal_force(mass_kg=10, radius_m=0.5, omega_rad_s=10)
    assert r['centrifugal_force_N'] == 500


def test_centrifugal_force_with_rpm():
    r = centrifugal_force(mass_kg=10, radius_m=0.5, rpm=300)
    assert r['centrifugal_force_N'] > 0


def test_centrifugal_force_with_v():
    r = centrifugal_force(mass_kg=10, radius_m=0.5, v_mps=10)
    assert r['centrifugal_force_N'] == 2000


# ----- 动量 (key: momentum_kgms) -----
def test_momentum():
    r = momentum(mass_kg=10, velocity_mps=5)
    assert r['momentum_kgms'] == 50
    assert r['kinetic_energy_J'] == 125


def test_angular_momentum():
    r = angular_momentum(I_kgm2=2, omega_rad_s=10)
    assert r['angular_momentum_kgm2s'] == 20


# ----- 冲量 (key: velocity_change_mps) -----
def test_impulse():
    r = impulse(force_N=100, time_s=2)
    assert r['impulse_Ns'] == 200


def test_impulse_with_mass():
    r = impulse(force_N=100, time_s=2, mass_kg=10)
    assert r['velocity_change_mps'] == 20


# ----- 功和能 (key: work_linear_J / work_rotational_J / kinetic_energy_J) -----
def test_work_energy_linear():
    r = work_energy(force_N=100, distance_m=5)
    assert r['work_linear_J'] == 500


def test_work_energy_torque():
    r = work_energy(torque_Nm=10, angle_rad=5)
    assert r['work_rotational_J'] == 50


def test_work_energy_kinetic():
    r = work_energy(mass_kg=10, velocity_mps=5)
    # Ek = 0.5·10·25 = 125
    assert r['kinetic_energy_J'] == 125


def test_work_energy_all():
    r = work_energy(force_N=100, distance_m=5, torque_Nm=10, angle_rad=5,
                    mass_kg=10, velocity_mps=5)
    assert r['work_linear_J'] == 500
    assert r['work_rotational_J'] == 50
    assert r['kinetic_energy_J'] == 125


def test_work_energy_no_input():
    r = work_energy()
    assert r == {}


# ----- 功率 (key: power_linear_W / power_rotational_W / power_work_W) -----
def test_power_calc_F_v():
    r = power_calc(force_N=100, velocity_mps=5)
    assert r['power_linear_W'] == 500
    assert r['power_linear_kW'] == 0.5


def test_power_calc_T_omega():
    r = power_calc(torque_Nm=10, omega_rad_s=10)
    assert r['power_rotational_W'] == 100


def test_power_calc_T_rpm():
    r = power_calc(torque_Nm=10, rpm=100)
    # P = T·2π·n/60 = 10·2π·100/60 ≈ 104.72
    assert r['power_rotational_W'] == pytest.approx(104.72, rel=1e-2)


def test_power_calc_work_time():
    r = power_calc(work_J=1000, time_s=2)
    assert r['power_work_W'] == 500


def test_power_calc_all():
    r = power_calc(force_N=100, velocity_mps=5, torque_Nm=10, omega_rad_s=10,
                   work_J=1000, time_s=2)
    assert r['power_linear_W'] == 500
    assert r['power_rotational_W'] == 100
    assert r['power_work_W'] == 500


# ----- 摩擦力 -----
def test_friction_static():
    r = friction(force_normal_N=100, mu_static=0.5)
    assert r['static_friction_N'] == 50


def test_friction_kinetic():
    r = friction(force_normal_N=100, mu_kinetic=0.4)
    assert r['kinetic_friction_N'] == 40


def test_friction_rolling():
    r = friction(force_normal_N=100, mu_rolling=0.001)
    assert r['rolling_friction_N'] == 0.1


def test_friction_all():
    r = friction(force_normal_N=100, mu_static=0.5, mu_kinetic=0.4, mu_rolling=0.001)
    assert r['static_friction_N'] == 50
    assert r['kinetic_friction_N'] == 40
    assert r['rolling_friction_N'] == 0.1


# ----- 转动惯量 (形状名: solid_cylinder, hollow_cylinder, solid_sphere, thin_sphere, ...) -----
def test_mass_inertia_solid_cylinder():
    r = mass_inertia('solid_cylinder', mass_kg=10, r=0.5)
    # I = 0.5·10·0.25 = 1.25
    assert r['I_axial_kgm2'] == 1.25


def test_mass_inertia_solid_cylinder_with_h():
    """带 h → 多返回 I_diametral_kgm2"""
    r = mass_inertia('solid_cylinder', mass_kg=10, r=0.5, h=1)
    assert 'I_diametral_kgm2' in r


def test_mass_inertia_disc():
    """'disc' 是 'solid_cylinder' 的别名"""
    r = mass_inertia('disc', mass_kg=10, r=0.5)
    assert r['I_axial_kgm2'] == 1.25


def test_mass_inertia_hollow_cylinder():
    r = mass_inertia('hollow_cylinder', mass_kg=10, r1=0.3, r2=0.5)
    # I = 0.5·10·(0.09+0.25) = 1.7
    assert r['I_axial_kgm2'] == 1.7


def test_mass_inertia_hollow_cylinder_with_h():
    r = mass_inertia('hollow_cylinder', mass_kg=10, r1=0.3, r2=0.5, h=1)
    assert r['I_axial_kgm2'] == 1.7


def test_mass_inertia_solid_sphere():
    r = mass_inertia('solid_sphere', mass_kg=10, r=0.5)
    # I = 0.4·10·0.25 = 1.0
    assert r['I_kgm2'] == 1.0


def test_mass_inertia_thin_sphere():
    r = mass_inertia('thin_sphere', mass_kg=10, r=0.5, t=0.01)
    # m = 4π·0.25·0.01 = 0.0314
    # I = 0.667·0.0314·0.25 = 0.00523
    assert r['I_kgm2'] > 0


def test_mass_inertia_thin_rod_center():
    r = mass_inertia('thin_rod_center', mass_kg=12, L=2, A=0.01)
    # I = 12·4/12 = 4
    assert r['I_kgm2'] == 4


def test_mass_inertia_thin_rod_end():
    r = mass_inertia('thin_rod_end', mass_kg=12, L=2, A=0.01)
    # I = 12·4/3 = 16
    assert r['I_kgm2'] == pytest.approx(16, rel=1e-3)


def test_mass_inertia_rectangular_plate():
    r = mass_inertia('rectangular_plate', mass_kg=12, a=2, b=3, t=0.01)
    # I = 12·(4+9)/12 = 13
    assert r['I_kgm2'] == 13
    assert 'I_x_kgm2' in r
    assert 'I_y_kgm2' in r


def test_mass_inertia_annulus():
    r = mass_inertia('annulus', mass_kg=10, r=0.5, A=0.001)
    # m = 2π·0.5·0.001 = 0.00314
    # I = m·r² = 0.00314·0.25 = 0.000785
    assert r['I_kgm2'] > 0


def test_mass_inertia_cone():
    r = mass_inertia('cone', mass_kg=10, r=0.5, h=1)
    # I = 0.3·10·0.25 = 0.75
    assert r['I_axial_kgm2'] == 0.75


def test_mass_inertia_rectangular_block():
    r = mass_inertia('rectangular_block', mass_kg=12, a=2, b=3, c=4)
    # I_z = 12·(4+9)/12 = 13
    assert r['I_z_kgm2'] == 13


def test_mass_inertia_parallel_axis():
    r = mass_inertia('parallel_axis', mass_kg=10, I_cm=2, d=1)
    # I = 2 + 10·1 = 12
    assert r['I_parallel_kgm2'] == 12


def test_mass_inertia_with_density():
    """用密度计算质量 - 函数内部用密度求 m, 不返回 mass_kg 字段, 只返回 I"""
    r = mass_inertia('solid_cylinder', density_kgm3=7800, r=0.5, h=0.1)
    # m = ρ·π·r²·h = 7800·π·0.25·0.1 ≈ 612.6
    # I = 0.5·m·r² ≈ 76.58
    assert r['I_axial_kgm2'] == pytest.approx(76.58, rel=1e-2)


def test_mass_inertia_unknown():
    r = mass_inertia('unknown_xxx', mass_kg=1)
    assert 'error' in r


# ----- 平行轴定理 -----
def test_parallel_axis_theorem():
    r = parallel_axis_theorem(I_cm=2, mass=10, d=1)
    assert r['I_parallel'] == 12


# ----- 回转半径 -----
def test_radius_of_gyration():
    r = radius_of_gyration(I=2, mass=10)
    # i = √(2/10) = 0.4472
    assert r['radius_of_gyration_m'] == pytest.approx(0.4472, abs=1e-3)


def test_radius_of_gyration_zero_mass():
    r = radius_of_gyration(I=2, mass=0)
    assert 'error' in r


# ----- 弹簧-质量振动 (key: natural_freq_rad_s / natural_freq_Hz / damped_freq_rad_s) -----
def test_spring_mass_vibration():
    r = spring_mass_vibration(k_Nm=1000, mass_kg=10, zeta=0.05)
    # omega_n = √(1000/10) = 10
    assert r['natural_freq_rad_s'] == 10
    assert r['natural_freq_Hz'] == pytest.approx(10/(2*math.pi), rel=1e-3)


def test_spring_mass_vibration_high_damping():
    """过阻尼"""
    r = spring_mass_vibration(k_Nm=1000, mass_kg=10, zeta=2.0)
    assert r['damped_freq_rad_s'] == 0


# ----- 扭转振动 (key: natural_freq_rad_s) -----
def test_torsional_vibration():
    r = torsional_vibration(G_mpa=80000, J_mm4=1e5, L_mm=1000, I_disc_kgm2=1)
    # G=8e10 Pa, J=1e-7 m^4, L=1 m, I=1
    # kt = GJ/L = 8000, omega = √(8000) ≈ 89.44
    assert r['natural_freq_rad_s'] == pytest.approx(89.44, rel=1e-2)


# ----- 临界转速 (key: critical_speed_rpm) -----
def test_critical_shaft_speed():
    r = critical_shaft_speed(E_mpa=200000, I_mm4=1e6, mass_kg=10, L_mm=1000)
    assert 'critical_speed_rpm' in r
    assert r['critical_speed_rpm'] > 0


# ----- 单摆 -----
def test_simple_pendulum():
    r = simple_pendulum(L_m=1)
    # T = 2π·√(1/9.81) ≈ 2.006
    assert r['period_s'] == pytest.approx(2.006, rel=1e-2)


# ----- 飞轮能量 (key: energy_J, energy_kJ) -----
def test_flywheel_energy_with_omega():
    r = flywheel_energy(I_kgm2=2, omega_rad_s=10)
    # E = 0.5·2·100 = 100 J
    assert r['energy_J'] == 100
    assert r['energy_kJ'] == 0.1


def test_flywheel_energy_with_rpm():
    r = flywheel_energy(I_kgm2=2, rpm=3000)
    # omega = 2π·50 ≈ 314.16
    # E = 0.5·2·314.16² ≈ 98702
    assert r['energy_J'] == pytest.approx(98702, rel=1e-2)


def test_flywheel_energy_zero():
    """未给 omega → 0"""
    r = flywheel_energy(I_kgm2=2)
    assert r['energy_J'] == 0


# ----- 制动转矩 -----
def test_brake_torque():
    r = brake_torque(force_N=100, radius_m=0.2, num_shoes=2, mu=0.4)
    # T = F·r·n·μ = 100·0.2·2·0.4 = 16
    assert r['brake_torque_Nm'] == 16


# ----- 丝杠效率 -----
def test_lead_screw_efficiency():
    r = lead_screw_efficiency(d_mm=20, pitch_mm=5, mu=0.1)
    assert 'efficiency' in r
    assert 0 < r['efficiency'] < 1


# ----- 螺旋千斤顶 -----
def test_screw_jack_torque_lifting():
    r = screw_jack_torque(load_N=10000, d_mm=20, pitch_mm=5, mu=0.15)
    # 提升力矩存在, 包含 lead_angle
    assert r['lifting_torque_Nm'] > 0
    assert r['lead_angle_deg'] > 0


# ----- 行星齿轮 (key: ratio_fixed_ring, ratio_fixed_sun, ratio_fixed_carrier) -----
def test_planetary_gear():
    r = planetary_gear(z_sun=20, z_ring=80, z_planet=30)
    # alpha = 80/20 = 4
    assert r['alpha'] == 4
    # ratio_fixed_ring = 1/(1+4) = 0.2
    assert r['ratio_fixed_ring'] == 0.2
    # ratio_fixed_sun = 4/5 = 0.8
    assert r['ratio_fixed_sun'] == 0.8


# ----- 定轴轮系 (teeth_list 是 [(z1, z2), ...] 列表) -----
def test_compound_gear_train():
    r = compound_gear_train(teeth_list=[(20, 40), (15, 45)])
    # i = (40/20) · (45/15) = 2 · 3 = 6
    assert r['total_ratio'] == 6
    assert len(r['stages']) == 2
