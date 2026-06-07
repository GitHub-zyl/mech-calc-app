"""单元测试: calculations/bearing_full.py

目标覆盖率: ≥90%
参考标准: GB/T 6391-2010 (ISO 281:2007), SKF综合型录

测试覆盖范围:
  - calc_bearing_life_modified: 修正额定寿命 (球/滚子轴承)
  - calc_bearing_min_load: 最小载荷要求
  - calc_bearing_speed_limit: 极限转速校核
  - 边界条件: 缺参、零值、不合理参数
  - 异常处理: 类型错误、负值、极端值
"""
import math
import pytest

from backend.calculations.bearing_full import (
    calc_bearing_life_modified,
    calc_bearing_min_load,
    calc_bearing_speed_limit,
)


# ==================== calc_bearing_life_modified ====================

class TestBearingLifeModifiedBasic:
    """基本额定寿命计算 - 正常路径."""

    def test_ball_bearing_basic(self):
        """球轴承 (p=3): 已知 C=10kN, P=5kN, n=3000rpm."""
        r = calc_bearing_life_modified(C=10.0, P=5.0, n=3000)
        # L10 = (10^6/(60·3000)) · (10/5)^3 = 5.556 · 8 = 44.44 h
        assert r['dynamic_load_C_kN'] == 10.0
        assert r['equivalent_load_P_kN'] == 5.0
        assert r['speed_n_rpm'] == 3000
        assert r['bearing_type'] == 'ball'
        assert r['exponent_p'] == 3.0
        # 期望 L10 ≈ 44.44 h
        assert r['basic_L10h'] == pytest.approx(44.44, rel=1e-2)
        # 默认 a1=a23=1.0, L_nmh == L10
        assert r['modified_Lnmh'] == pytest.approx(44.44, rel=1e-2)

    def test_roller_bearing_basic(self):
        """滚子轴承 (p=10/3): 已知 C=20kN, P=10kN, n=1500rpm."""
        r = calc_bearing_life_modified(C=20.0, P=10.0, n=1500, bearing_type='roller')
        # L10 = (10^6/(60·1500)) · (20/10)^(10/3) = 11.111 · 10.079 ≈ 112 h
        assert r['exponent_p'] == pytest.approx(10/3, rel=1e-6)
        # (20/10)^(10/3) = 2^3.333 ≈ 10.0794
        expected = (10**6 / (60 * 1500)) * (20/10) ** (10/3)
        assert r['basic_L10h'] == pytest.approx(expected, rel=1e-3)

    def test_modified_with_reliability_95(self):
        """95% 可靠度 (a1=0.62): 寿命缩短."""
        r_normal = calc_bearing_life_modified(C=10.0, P=5.0, n=3000, a1=1.0)
        r_95 = calc_bearing_life_modified(C=10.0, P=5.0, n=3000, a1=0.62)
        # 95% 可靠度寿命 < 90% 可靠度寿命
        assert r_95['modified_Lnmh'] < r_normal['modified_Lnmh']
        assert r_95['modified_Lnmh'] == pytest.approx(
            0.62 * r_normal['basic_L10h'], rel=1e-2
        )

    def test_modified_with_reliability_99(self):
        """99% 可靠度 (a1=0.33): 寿命进一步缩短."""
        r = calc_bearing_life_modified(C=10.0, P=5.0, n=3000, a1=0.33)
        assert r['reliability_factor_a1'] == 0.33
        assert r['modified_Lnmh'] == pytest.approx(0.33 * 44.44, rel=1e-2)

    def test_modified_with_lubrication_factor(self):
        """润滑/材料修正系数 (a23=2.0): 寿命延长 2x."""
        r = calc_bearing_life_modified(C=10.0, P=5.0, n=3000, a23=2.0)
        assert r['lubrication_factor_a23'] == 2.0
        assert r['modified_Lnmh'] == pytest.approx(2 * 44.44, rel=1e-2)

    def test_combined_modification_factors(self):
        """组合修正系数 a1=0.62, a23=1.5: 寿命 0.93x."""
        r = calc_bearing_life_modified(C=10.0, P=5.0, n=3000, a1=0.62, a23=1.5)
        assert r['modified_Lnmh'] == pytest.approx(0.62 * 1.5 * 44.44, rel=1e-2)

    def test_returns_required_keys(self):
        """返回结果包含所有必需字段."""
        r = calc_bearing_life_modified(C=10.0, P=5.0, n=3000)
        required = [
            'dynamic_load_C_kN', 'equivalent_load_P_kN', 'speed_n_rpm',
            'bearing_type', 'exponent_p', 'reliability_factor_a1',
            'lubrication_factor_a23', 'basic_L10h', 'modified_Lnmh',
            'formula', 'reference'
        ]
        for key in required:
            assert key in r, f"Missing key: {key}"


class TestBearingLifeModifiedEdgeCases:
    """基本额定寿命计算 - 边界与异常."""

    def test_missing_c_parameter(self):
        """缺 C 参数: 返回 error."""
        r = calc_bearing_life_modified(P=5.0, n=3000)
        assert 'error' in r
        assert 'C' in r['error']

    def test_missing_p_parameter(self):
        """缺 P 参数: 返回 error."""
        r = calc_bearing_life_modified(C=10.0, n=3000)
        assert 'error' in r

    def test_missing_n_parameter(self):
        """缺 n 参数: 返回 error."""
        r = calc_bearing_life_modified(C=10.0, P=5.0)
        assert 'error' in r

    def test_zero_n_speed(self):
        """转速为 0: 触发缺参错误 (not 0 == True)."""
        r = calc_bearing_life_modified(C=10.0, P=5.0, n=0)
        # n=0 被 `not n` 判定为缺参
        assert 'error' in r

    def test_zero_p_load(self):
        """当量动载荷为 0: 触发缺参错误."""
        r = calc_bearing_life_modified(C=10.0, P=0, n=3000)
        assert 'error' in r

    def test_c_equals_p(self):
        """C = P: 寿命因子为 1, 经 round(L10, 1) 保留 1 位小数."""
        r = calc_bearing_life_modified(C=5.0, P=5.0, n=3000)
        # (5/5)^3 = 1, L10 = 10^6/(60·3000) · 1 = 5.5556
        # round(5.5556, 1) = 5.6
        assert r['basic_L10h'] == pytest.approx(5.6, rel=1e-2)

    def test_high_load_low_life(self):
        """高载荷 (P > C): 寿命极低 (立方关系)."""
        r = calc_bearing_life_modified(C=5.0, P=10.0, n=3000)
        # (5/10)^3 = 0.125, L10 = 5.556 · 0.125 ≈ 0.694 h
        assert r['basic_L10h'] == pytest.approx(0.694, rel=1e-2)

    def test_high_speed_low_life(self):
        """高转速: 寿命与转速成反比."""
        r1 = calc_bearing_life_modified(C=10.0, P=5.0, n=1000)
        r2 = calc_bearing_life_modified(C=10.0, P=5.0, n=2000)
        # 转速翻倍, 寿命减半
        assert r2['basic_L10h'] == pytest.approx(r1['basic_L10h'] / 2, rel=1e-2)


# ==================== calc_bearing_min_load ====================

class TestBearingMinLoad:
    """最小载荷要求计算."""

    def test_ball_bearing_basic(self):
        """球轴承基本: Fm = 0.01·C0."""
        r = calc_bearing_min_load(C0=20.0, bearing_type='ball')
        assert r['min_radial_load_Fm_kN'] == pytest.approx(0.2, rel=1e-3)
        assert r['static_load_C0_kN'] == 20.0
        assert r['bearing_type'] == 'ball'

    def test_roller_bearing_basic(self):
        """滚子轴承基本: Fm = 0.02·C0."""
        r = calc_bearing_min_load(C0=20.0, bearing_type='roller')
        assert r['min_radial_load_Fm_kN'] == pytest.approx(0.4, rel=1e-3)
        assert r['bearing_type'] == 'roller'

    def test_ball_bearing_large_dm(self):
        """球轴承 dm >= 100: 系数 (dm/100)^0.5."""
        r = calc_bearing_min_load(C0=20.0, dm=200, bearing_type='ball')
        # Fm = 0.2 · (200/100)^0.5 = 0.2 · 1.414 ≈ 0.283
        assert r['min_radial_load_Fm_kN'] == pytest.approx(0.283, rel=1e-2)
        assert r['pitch_diameter_dm_mm'] == 200

    def test_ball_bearing_high_speed(self):
        """球轴承 n >= 1000: 系数 (n/1000)^0.5."""
        r = calc_bearing_min_load(C0=20.0, n=2000, bearing_type='ball')
        # Fm = 0.2 · (2000/1000)^0.5 = 0.2 · 1.414 ≈ 0.283
        assert r['min_radial_load_Fm_kN'] == pytest.approx(0.283, rel=1e-2)

    def test_ball_bearing_combined_factors(self):
        """球轴承 dm=200 + n=2000: 两个修正同时应用."""
        r = calc_bearing_min_load(C0=20.0, dm=200, n=2000, bearing_type='ball')
        # Fm = 0.2 · (200/100)^0.5 · (2000/1000)^0.5 = 0.2 · 1.414 · 1.414 ≈ 0.4
        assert r['min_radial_load_Fm_kN'] == pytest.approx(0.4, rel=1e-2)

    def test_roller_bearing_large_dm(self):
        """滚子轴承 dm >= 100: 系数 (dm/100)^0.33."""
        r = calc_bearing_min_load(C0=20.0, dm=200, bearing_type='roller')
        # Fm = 0.4 · (200/100)^0.33 ≈ 0.4 · 1.26 ≈ 0.504
        assert r['min_radial_load_Fm_kN'] == pytest.approx(0.504, rel=1e-2)

    def test_missing_c0_parameter(self):
        """缺 C0: 返回 error."""
        r = calc_bearing_min_load()
        assert 'error' in r
        assert 'C0' in r['error']

    def test_returns_required_keys(self):
        """返回结果包含必需字段."""
        r = calc_bearing_min_load(C0=20.0, dm=100, n=1500)
        for key in ['static_load_C0_kN', 'bearing_type', 'pitch_diameter_dm_mm',
                     'speed_n_rpm', 'min_radial_load_Fm_kN', 'formula', 'reference']:
            assert key in r, f"Missing key: {key}"


# ==================== calc_bearing_speed_limit ====================

class TestBearingSpeedLimit:
    """极限转速校核."""

    def test_deep_groove_ball_grease_safe(self):
        """深沟球轴承 + 脂润滑, 低速: 安全."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='deep_groove_ball',
                                        lubrication='grease')
        # actual_ndm = 1000 · 100 = 100000
        # limit = 500000 · 1.0 = 500000
        # safety = 500000 / 100000 = 5.0
        assert r['actual_ndm'] == 100000.0
        assert r['limit_ndm'] == 500000.0
        assert r['safety_ratio'] == pytest.approx(5.0, rel=1e-2)
        assert r['is_safe'] is True

    def test_above_limit_unsafe(self):
        """超出极限: 不安全."""
        r = calc_bearing_speed_limit(dm=100, n=6000, bearing_type='deep_groove_ball',
                                        lubrication='grease')
        # actual_ndm = 600000 > limit 500000
        assert r['is_safe'] is False
        assert r['safety_ratio'] < 1.0

    def test_oil_jet_lubrication_increases_limit(self):
        """油雾喷射润滑 (factor=2.5): 极限 2.5x."""
        r_grease = calc_bearing_speed_limit(dm=100, n=3000, bearing_type='deep_groove_ball',
                                               lubrication='grease')
        r_jet = calc_bearing_speed_limit(dm=100, n=3000, bearing_type='deep_groove_ball',
                                            lubrication='oil_jet')
        # 油雾喷射润滑下 limit = 500000 · 2.5 = 1250000
        assert r_jet['limit_ndm'] == pytest.approx(1250000.0, rel=1e-2)
        assert r_jet['safety_ratio'] == pytest.approx(r_grease['safety_ratio'] * 2.5, rel=1e-2)

    def test_oil_bath_lubrication(self):
        """油浴润滑 (factor=1.5)."""
        r = calc_bearing_speed_limit(dm=100, n=3000, bearing_type='deep_groove_ball',
                                        lubrication='oil_bath')
        assert r['lubrication'] == 'oil_bath'
        assert r['limit_ndm'] == pytest.approx(500000 * 1.5, rel=1e-2)

    def test_oil_mist_lubrication(self):
        """油雾润滑 (factor=2.0)."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='deep_groove_ball',
                                        lubrication='oil_mist')
        assert r['lubrication'] == 'oil_mist'
        assert r['limit_ndm'] == pytest.approx(500000 * 2.0, rel=1e-2)

    def test_tapered_roller_bearing(self):
        """圆锥滚子轴承: 基线 250000."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='tapered_roller')
        assert r['bearing_type'] == 'tapered_roller'
        assert r['limit_ndm'] == 250000.0

    def test_cylindrical_roller_bearing(self):
        """圆柱滚子轴承: 基线 350000."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='cylindrical_roller')
        assert r['limit_ndm'] == 350000.0

    def test_thrust_ball_bearing(self):
        """推力球轴承: 基线 200000."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='thrust_ball')
        assert r['limit_ndm'] == 200000.0

    def test_angular_contact_bearing(self):
        """角接触球轴承: 基线 450000."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='angular_contact')
        assert r['limit_ndm'] == 450000.0

    def test_spherical_roller_bearing(self):
        """调心滚子轴承: 基线 200000."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='spherical_roller')
        assert r['limit_ndm'] == 200000.0

    def test_unknown_bearing_type_default(self):
        """未知类型: 使用默认基线 300000."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='unknown_type_xyz')
        assert r['limit_ndm'] == 300000.0

    def test_unknown_lubrication_default(self):
        """未知润滑: 使用默认系数 1.0."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='deep_groove_ball',
                                        lubrication='unknown_lube')
        assert r['limit_ndm'] == 500000.0  # 仅基线, 不乘系数

    def test_missing_dm(self):
        """缺 dm: 返回 error."""
        r = calc_bearing_speed_limit(n=1000)
        assert 'error' in r
        assert 'dm' in r['error']

    def test_missing_n(self):
        """缺 n: 返回 error."""
        r = calc_bearing_speed_limit(dm=100)
        assert 'error' in r

    def test_zero_dm(self):
        """dm=0: 视为缺参."""
        r = calc_bearing_speed_limit(dm=0, n=1000)
        assert 'error' in r

    def test_zero_n_safety_infinity(self):
        """n=0: 触发缺参错误 (not 0 == True)."""
        r = calc_bearing_speed_limit(dm=100, n=0, bearing_type='deep_groove_ball')
        # n=0 被 `not n` 判定为缺参
        assert 'error' in r

    def test_returns_required_keys(self):
        """返回结果包含必需字段."""
        r = calc_bearing_speed_limit(dm=100, n=1000, bearing_type='deep_groove_ball')
        for key in ['bearing_type', 'lubrication', 'pitch_diameter_dm_mm',
                     'actual_speed_n_rpm', 'actual_ndm', 'limit_ndm',
                     'safety_ratio', 'is_safe', 'formula', 'reference']:
            assert key in r, f"Missing key: {key}"

    def test_edge_case_at_limit(self):
        """边界: 正好等于极限, safety=1.0."""
        # limit=500000, actual=500000, safety=1.0
        r = calc_bearing_speed_limit(dm=100, n=5000, bearing_type='deep_groove_ball',
                                        lubrication='grease')
        assert r['safety_ratio'] == pytest.approx(1.0, rel=1e-2)
        # is_safe = safety >= 1.0
        assert r['is_safe'] is True
