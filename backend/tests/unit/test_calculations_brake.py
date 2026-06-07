"""单元测试: calculations/brake.py

目标覆盖率: ≥80%
参考标准: 机械设计手册(成大先)第16篇 §14, 第18篇 §10

测试覆盖范围:
  - calc_disc_brake_torque: 盘式制动器 (均匀磨损假设)
  - calc_band_brake_torque: 带式制动器 (欧拉公式)
  - calc_clutch_energy: 离合器接合滑磨功与温升
  - 边界条件: 缺参、零值、不合理参数
  - 异常处理: 外径≤内径、负值、极端值
"""
import math
import pytest

from backend.calculations.brake import (
    calc_disc_brake_torque,
    calc_band_brake_torque,
    calc_clutch_energy,
)


# ==================== calc_disc_brake_torque ====================

class TestDiscBrakeTorqueBasic:
    """盘式制动器 - 正常路径."""

    def test_basic_disc_brake(self):
        """基本盘式制动器: p=1MPa, μ=0.4, D_o=300mm, D_i=200mm, n_faces=2."""
        r = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300, D_i=200, n_faces=2)
        # T_N_mm = 2 · 0.4 · 1 · π · (300³ - 200³) / 12
        # = 0.8 · π · (27000000 - 8000000) / 12
        # = 0.8 · π · 19000000 / 12
        # ≈ 3979342.17 N·mm = 3979.34 N·m
        expected_torque = 2 * 0.4 * 1.0 * math.pi * (300**3 - 200**3) / 12
        assert r['torque_N_mm'] == pytest.approx(expected_torque, rel=1e-3)
        assert r['torque_N_m'] == pytest.approx(expected_torque / 1000, rel=1e-3)
        assert r['pressure_MPa'] == 1.0
        assert r['friction_coeff_mu'] == 0.4
        assert r['disc_OD_mm'] == 300
        assert r['disc_ID_mm'] == 200
        assert r['num_faces'] == 2

    def test_single_face(self):
        """单面摩擦 (n_faces=1): 扭矩减半."""
        r_two = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300, D_i=200, n_faces=2)
        r_one = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300, D_i=200, n_faces=1)
        assert r_one['torque_N_m'] == pytest.approx(r_two['torque_N_m'] / 2, rel=1e-3)

    def test_multi_disc(self):
        """多盘 (n_faces=4): 扭矩 2x."""
        r_two = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300, D_i=200, n_faces=2)
        r_four = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300, D_i=200, n_faces=4)
        assert r_four['torque_N_m'] == pytest.approx(r_two['torque_N_m'] * 2, rel=1e-3)

    def test_higher_pressure(self):
        """更高比压: 扭矩线性增加."""
        r1 = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300, D_i=200)
        r2 = calc_disc_brake_torque(p=2.0, mu=0.4, D_o=300, D_i=200)
        assert r2['torque_N_m'] == pytest.approx(r1['torque_N_m'] * 2, rel=1e-3)

    def test_higher_friction(self):
        """更高摩擦系数: 扭矩线性增加."""
        r1 = calc_disc_brake_torque(p=1.0, mu=0.3, D_o=300, D_i=200)
        r2 = calc_disc_brake_torque(p=1.0, mu=0.6, D_o=300, D_i=200)
        assert r2['torque_N_m'] == pytest.approx(r1['torque_N_m'] * 2, rel=1e-3)

    def test_effective_radius(self):
        """有效摩擦半径: R_eff = (D_o³-D_i³) / (3·(D_o²-D_i²))."""
        r = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300, D_i=200)
        expected_R = (300**3 - 200**3) / (3 * (300**2 - 200**2))
        assert r['effective_radius_mm'] == pytest.approx(expected_R, rel=1e-3)

    def test_returns_required_keys(self):
        """返回结果包含所有必需字段."""
        r = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300, D_i=200)
        required = ['pressure_MPa', 'friction_coeff_mu', 'disc_OD_mm', 'disc_ID_mm',
                     'num_faces', 'effective_radius_mm', 'torque_N_mm', 'torque_N_m',
                     'formula', 'reference']
        for key in required:
            assert key in r, f"Missing key: {key}"


class TestDiscBrakeTorqueEdgeCases:
    """盘式制动器 - 边界与异常."""

    def test_missing_p(self):
        """缺 p: 返回 error."""
        r = calc_disc_brake_torque(mu=0.4, D_o=300, D_i=200)
        assert 'error' in r
        assert 'p' in r['error']

    def test_missing_mu(self):
        """缺 μ: 返回 error."""
        r = calc_disc_brake_torque(p=1.0, D_o=300, D_i=200)
        assert 'error' in r

    def test_missing_D_o(self):
        """缺 D_o: 返回 error."""
        r = calc_disc_brake_torque(p=1.0, mu=0.4, D_i=200)
        assert 'error' in r

    def test_missing_D_i(self):
        """缺 D_i: 返回 error."""
        r = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300)
        assert 'error' in r

    def test_D_i_equals_D_o(self):
        """D_i == D_o: 触发外径必须大于内径错误 (>= 检查)."""
        r = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=300, D_i=300)
        # D_i >= D_o 触发错误
        assert 'error' in r
        assert '外径' in r['error']

    def test_D_i_greater_than_D_o(self):
        """D_i > D_o: 物理不合理, 返回 error."""
        r = calc_disc_brake_torque(p=1.0, mu=0.4, D_o=200, D_i=300)
        assert 'error' in r
        assert '外径' in r['error']


# ==================== calc_band_brake_torque ====================

class TestBandBrakeTorqueBasic:
    """带式制动器 - 正常路径."""

    def test_basic_band_brake(self):
        """基本带式制动器: F1=1000N, μ=0.3, θ=270°, r=150mm."""
        r = calc_band_brake_torque(F1=1000, mu=0.3, theta_deg=270, r=150)
        # theta_rad = 270 · π / 180 = 4.712
        # ratio = e^(0.3 · 4.712) = e^1.4136 ≈ 4.110
        # F2 = 1000 / 4.110 ≈ 243.30 N
        # T = (1000 - 243.30) · 150 = 113505.4 N·mm = 113.5 N·m
        theta_rad = 270 * math.pi / 180
        ratio = math.exp(0.3 * theta_rad)
        F2_expected = 1000 / ratio
        T_expected = (1000 - F2_expected) * 150
        assert r['slack_force_F2_N'] == pytest.approx(F2_expected, rel=1e-2)
        assert r['torque_N_mm'] == pytest.approx(T_expected, rel=1e-2)
        assert r['torque_N_m'] == pytest.approx(T_expected / 1000, rel=1e-2)
        assert r['F1_F2_ratio'] == pytest.approx(ratio, rel=1e-2)
        assert r['wrap_angle_theta_rad'] == pytest.approx(theta_rad, rel=1e-3)

    def test_self_locking_detected(self):
        """自锁条件: μ·θ >= 3.0 (θ=270°, μ=0.4 -> 1.884, 未自锁)."""
        r = calc_band_brake_torque(F1=1000, mu=0.4, theta_deg=270, r=150)
        # μ·θ = 0.4 · 4.712 = 1.885 < 3.0 (不自锁)
        assert r['is_self_locking'] is False

    def test_self_locking_at_large_wrap(self):
        """自锁: 大包角 + 高摩擦 (θ=540°, μ=0.6 -> 5.65 > 3.0)."""
        r = calc_band_brake_torque(F1=1000, mu=0.6, theta_deg=540, r=150)
        # μ·θ = 0.6 · 9.425 = 5.655 > 3.0 (自锁)
        assert r['is_self_locking'] is True

    def test_self_locking_at_high_friction(self):
        """自锁: 高摩擦 (θ=180°, μ=1.0 -> 3.14 > 3.0)."""
        r = calc_band_brake_torque(F1=1000, mu=1.0, theta_deg=180, r=150)
        assert r['is_self_locking'] is True

    def test_higher_friction_more_torque(self):
        """更高摩擦: F1/F2 比更大, 扭矩更大."""
        r1 = calc_band_brake_torque(F1=1000, mu=0.2, theta_deg=270, r=150)
        r2 = calc_band_brake_torque(F1=1000, mu=0.5, theta_deg=270, r=150)
        assert r2['torque_N_m'] > r1['torque_N_m']
        assert r2['F1_F2_ratio'] > r1['F1_F2_ratio']

    def test_larger_drum_more_torque(self):
        """更大制动鼓: 扭矩线性增加."""
        r1 = calc_band_brake_torque(F1=1000, mu=0.3, theta_deg=270, r=100)
        r2 = calc_band_brake_torque(F1=1000, mu=0.3, theta_deg=270, r=200)
        assert r2['torque_N_m'] == pytest.approx(r1['torque_N_m'] * 2, rel=1e-3)

    def test_zero_wrap_angle(self):
        """包角为 0: 触发缺参错误 (not 0 == True)."""
        r = calc_band_brake_torque(F1=1000, mu=0.3, theta_deg=0, r=150)
        # not 0 == True, 触发错误
        assert 'error' in r

    def test_returns_required_keys(self):
        """返回结果包含所有必需字段."""
        r = calc_band_brake_torque(F1=1000, mu=0.3, theta_deg=270, r=150)
        required = ['tight_force_F1_N', 'friction_coeff_mu', 'wrap_angle_theta_deg',
                     'wrap_angle_theta_rad', 'drum_radius_r_mm', 'slack_force_F2_N',
                     'F1_F2_ratio', 'torque_N_mm', 'torque_N_m',
                     'is_self_locking', 'formula', 'reference']
        for key in required:
            assert key in r, f"Missing key: {key}"


class TestBandBrakeTorqueEdgeCases:
    """带式制动器 - 边界与异常."""

    def test_missing_F1(self):
        """缺 F1: 返回 error."""
        r = calc_band_brake_torque(mu=0.3, theta_deg=270, r=150)
        assert 'error' in r
        assert 'F1' in r['error']

    def test_missing_mu(self):
        """缺 μ: 返回 error."""
        r = calc_band_brake_torque(F1=1000, theta_deg=270, r=150)
        assert 'error' in r

    def test_missing_theta(self):
        """缺 θ: 返回 error."""
        r = calc_band_brake_torque(F1=1000, mu=0.3, r=150)
        assert 'error' in r

    def test_missing_r(self):
        """缺 r: 返回 error."""
        r = calc_band_brake_torque(F1=1000, mu=0.3, theta_deg=270)
        assert 'error' in r


# ==================== calc_clutch_energy ====================

class TestClutchEnergyBasic:
    """离合器滑磨功与温升 - 正常路径."""

    def test_with_slip_work_direct(self):
        """直接提供滑磨功: 不需要 J 和 omega."""
        r = calc_clutch_energy(W=5000.0)
        assert r['slip_work_J'] == 5000.0
        assert r['slip_work_kJ'] == 5.0

    def test_with_slip_work_and_temp_rise(self):
        """提供 W + 鼓质量: 计算温升."""
        r = calc_clutch_energy(W=50000.0, m_drum=10.0, c_specific=500)
        # ΔT = 50000 / (10 · 500) = 10 K
        assert r['slip_work_J'] == 50000.0
        assert r['temperature_rise_K'] == 10.0
        assert r['temperature_rise_acceptable'] is True
        assert r['drum_mass_kg'] == 10.0
        assert r['specific_heat_J_kgK'] == 500

    def test_with_inertia_and_omega1(self):
        """使用 J 和 ω1: 滑磨功 = 0.5·J·ω1² (从动件静止)."""
        r = calc_clutch_energy(J=1.0, omega1=100.0, m_drum=5.0)
        # W = 0.5 · 1.0 · (100² - 0²) = 5000 J
        # omega2 默认为 0
        assert r['slip_work_J'] == 5000.0
        assert r['inertia_J_kgm2'] == 1.0
        assert r['omega1_rad_s'] == 100.0
        assert r['omega2_rad_s'] == 0
        # ΔT = 5000 / (5 · 500) = 2 K
        assert r['temperature_rise_K'] == 2.0

    def test_with_inertia_and_both_omegas(self):
        """使用 J 和 ω1, ω2: 滑磨功 = 0.5·J·(ω1²-ω2²)."""
        r = calc_clutch_energy(J=1.0, omega1=100.0, omega2=50.0)
        # W = 0.5 · 1 · (100² - 50²) = 0.5 · 7500 = 3750 J
        assert r['slip_work_J'] == 3750.0
        assert r['omega1_rad_s'] == 100.0
        assert r['omega2_rad_s'] == 50.0

    def test_high_temp_above_acceptable(self):
        """温升 > 150K: 标记不可接受."""
        # 100000 J 能量, 1kg 鼓 -> 200K > 150K
        r = calc_clutch_energy(W=100000.0, m_drum=1.0, c_specific=500)
        assert r['temperature_rise_K'] == 200.0
        assert r['temperature_rise_acceptable'] is False

    def test_temp_acceptable_boundary(self):
        """温升 = 150K (干式极限)."""
        r = calc_clutch_energy(W=75000.0, m_drum=1.0, c_specific=500)
        assert r['temperature_rise_K'] == 150.0
        assert r['temperature_rise_acceptable'] is True  # <= 150

    def test_custom_specific_heat(self):
        """自定义比热: 铸铁 (c=460)."""
        r = calc_clutch_energy(W=46000.0, m_drum=1.0, c_specific=460)
        # ΔT = 46000 / (1 · 460) = 100 K
        assert r['temperature_rise_K'] == 100.0
        assert r['specific_heat_J_kgK'] == 460

    def test_no_temp_without_drum_mass(self):
        """不提供 m_drum: 不计算温升."""
        r = calc_clutch_energy(W=5000.0)
        assert 'temperature_rise_K' not in r

    def test_zero_drum_mass_skips_temp(self):
        """m_drum=0: 跳过温升计算 (除零保护)."""
        r = calc_clutch_energy(W=5000.0, m_drum=0)
        assert 'temperature_rise_K' not in r

    def test_returns_required_keys(self):
        """返回结果包含必需字段 (无温升)."""
        r = calc_clutch_energy(W=5000.0)
        for key in ['slip_work_J', 'slip_work_kJ', 'formula', 'reference']:
            assert key in r, f"Missing key: {key}"

    def test_returns_required_keys_with_temp(self):
        """返回结果包含必需字段 (有温升)."""
        r = calc_clutch_energy(W=5000.0, m_drum=10.0, c_specific=500)
        for key in ['slip_work_J', 'slip_work_kJ', 'drum_mass_kg',
                     'specific_heat_J_kgK', 'temperature_rise_K',
                     'temperature_rise_acceptable', 'note',
                     'formula', 'reference']:
            assert key in r, f"Missing key: {key}"


class TestClutchEnergyEdgeCases:
    """离合器滑磨功 - 边界与异常."""

    def test_missing_both_W_and_inertia(self):
        """同时缺 W 和 J: 返回 error."""
        r = calc_clutch_energy(m_drum=10.0)
        assert 'error' in r
        assert 'W' in r['error'] or 'J' in r['error']

    def test_only_inertia_without_omega1(self):
        """只提供 J 不提供 ω1: 返回 error (缺 omega1)."""
        r = calc_clutch_energy(J=1.0)
        assert 'error' in r
