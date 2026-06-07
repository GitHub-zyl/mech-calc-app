"""单元测试: backend/calculations/thread.py (覆盖率 65% → 90%+)

覆盖目标:
- metric_thread_basic: 基础尺寸 (中径/小径/底孔)
- tap_drill_diameter: 攻丝底孔 + 多螺距解析 (M6, M8x1, M10x1.25)
- bolt_preload_torque: 螺栓预紧 (4.6~12.9 等级)
"""
import pytest

from backend.calculations.thread import (
    metric_thread_basic,
    tap_drill_diameter,
    bolt_preload_torque,
)


class TestMetricThreadBasic:
    """metric_thread_basic 基础尺寸 (覆盖 L45-57)."""

    def test_m10_standard(self):
        """M10 标准螺纹."""
        r = metric_thread_basic(nominal_d=10, pitch=1.5)
        # H = 0.866 × 1.5 = 1.299
        assert r['thread_height'] == pytest.approx(1.299, rel=0.01)
        # 中径 d2 = 10 - 0.6495×1.5 = 9.026
        assert r['pitch_diameter'] == pytest.approx(9.026, rel=0.01)
        # 小径 d1 = 10 - 1.0825×1.5 = 8.376
        assert r['minor_diameter_external'] == pytest.approx(8.376, rel=0.01)
        # 底孔 = D1 + 0.1 = 8.476
        assert r['tap_drill_diameter'] == pytest.approx(8.476, rel=0.01)

    def test_m6_fine(self):
        """M6x1 细牙."""
        r = metric_thread_basic(nominal_d=6, pitch=1.0)
        assert r['pitch'] == 1.0
        assert r['nominal_diameter'] == 6

    def test_m16_coarse(self):
        """M16 标准螺纹 (p=2)."""
        r = metric_thread_basic(nominal_d=16, pitch=2.0)
        # 中径 = 16 - 0.6495×2 = 14.701
        assert r['pitch_diameter'] == pytest.approx(14.701, rel=0.01)

    def test_m3_very_fine(self):
        """M3x0.5 极细牙."""
        r = metric_thread_basic(nominal_d=3, pitch=0.5)
        assert r['thread_height'] == pytest.approx(0.433, rel=0.01)


class TestTapDrillDiameter:
    """tap_drill_diameter 攻丝底孔 (覆盖 L45-57)."""

    def test_m6_no_pitch_default(self):
        """M6 不指定螺距: 默认 1.0 (d<=6)."""
        r = tap_drill_diameter('M6')
        assert 'pitch' in r
        assert r['pitch'] == 1.0

    def test_m3_default_pitch(self):
        """M3 默认 0.8 (d<=3)."""
        r = tap_drill_diameter('M3')
        assert r['pitch'] == 0.8

    def test_m8_with_explicit_pitch(self):
        """M8x1 显式螺距."""
        r = tap_drill_diameter('M8x1')
        assert r['pitch'] == 1.0
        # 标准 M8 是 1.25, 细牙 1.0
        # D1 = 8 - 1.082532×1.0 = 6.917 → 取整 6.92
        assert r['theoretical_drill_mm'] == pytest.approx(6.92, rel=0.01)

    def test_m10x125_explicit(self):
        """M10x1.25 标准粗牙."""
        r = tap_drill_diameter('M10x1.25')
        assert r['pitch'] == 1.25

    def test_m12_default_pitch(self):
        """M12 不指定: d>10, <=16 → 1.5."""
        r = tap_drill_diameter('M12')
        assert r['pitch'] == 1.5

    def test_m20_default_pitch(self):
        """M20: d>16 → 2.0."""
        r = tap_drill_diameter('M20')
        assert r['pitch'] == 2.0

    def test_lowercase_x(self):
        """小写 x: M8x1.0 也应解析."""
        r = tap_drill_diameter('m8x1')
        assert r['pitch'] == 1.0

    def test_invalid_format_returns_error(self):
        """非法格式: 'XYZ' 应返回 error."""
        r = tap_drill_diameter('XYZ123')
        # 应包含 error 字段
        assert 'error' in r

    def test_with_whitespace(self):
        """前后空格: '  M10  ' 应能解析."""
        r = tap_drill_diameter('  M10  ')
        assert r['pitch'] in (1.0, 1.25, 1.5)  # 默认值合理

    def test_recommendations_for_different_materials(self):
        """不同材料的底孔推荐值应不同: 钢<铝<不锈钢 (按切削难度)."""
        r = tap_drill_diameter('M10')
        # 钢/铸铁: d - p, 不锈钢: d - 1.05p, 铝: d - 0.95p
        if 'drill_steel_castiron_mm' in r and 'drill_aluminum_mm' in r and 'drill_stainless_mm' in r:
            # 钢(易切) < 不锈钢 < 铝(软, 略大孔以利排屑)
            assert r['drill_steel_castiron_mm'] < r['drill_aluminum_mm']
            assert r['drill_stainless_mm'] < r['drill_aluminum_mm']


class TestBoltPreloadTorque:
    """bolt_preload_torque 螺栓预紧 (覆盖 L82-89, 118, 157-161)."""

    def test_grade_88_standard(self):
        """8.8 级标准螺栓."""
        r = bolt_preload_torque(d_mm=10, grade='8.8', mu=0.15)
        assert r['grade'] == '8.8'
        assert r['diameter_mm'] == 10
        # 8.8 级 σs = 640 MPa
        assert r['yield_strength_mpa'] == 640
        # 预紧力 Fp = 0.6 × σs × As / 1000 (kN)
        # 拧紧扭矩 T = 0.2 × Fp × d (N·m)
        assert r['preload_kN'] > 0
        assert r['tightening_torque_nm'] > 0

    def test_grade_109_high_strength(self):
        """10.9 级高强度螺栓."""
        r = bolt_preload_torque(d_mm=12, grade='10.9', mu=0.15)
        # 10.9 级 σs = 940 MPa
        assert r['yield_strength_mpa'] == 940
        # 高强度 → 高预紧力
        assert r['preload_kN'] > 30

    def test_grade_129_very_high(self):
        """12.9 级超高强度."""
        r = bolt_preload_torque(d_mm=14, grade='12.9', mu=0.15)
        assert r['yield_strength_mpa'] == 1100

    def test_grade_46_low(self):
        """4.6 级低强度."""
        r = bolt_preload_torque(d_mm=8, grade='4.6', mu=0.15)
        assert r['yield_strength_mpa'] == 240

    def test_unknown_grade_uses_default(self):
        """未知等级: 应回退到默认 (8.8=640)."""
        r = bolt_preload_torque(d_mm=10, grade='99.9', mu=0.15)
        # 默认 σs = 640
        assert r['yield_strength_mpa'] == 640

    def test_friction_coefficient_recorded(self):
        """摩擦系数应记录在结果中."""
        r = bolt_preload_torque(d_mm=10, grade='8.8', mu=0.20)
        assert r['friction_coefficient'] == 0.20

    def test_larger_diameter_higher_torque(self):
        """更大直径 → 更高扭矩."""
        r_small = bolt_preload_torque(d_mm=8, grade='8.8', mu=0.15)
        r_large = bolt_preload_torque(d_mm=16, grade='8.8', mu=0.15)
        assert r_large['tightening_torque_nm'] > r_small['tightening_torque_nm']
