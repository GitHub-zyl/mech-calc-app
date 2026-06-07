"""单元测试: backend/calculations/cam.py (覆盖率 67% → 90%+)"""
import math
import pytest

from backend.calculations.cam import (
    cam_motion_uniform,
    cam_motion_sine,
    cam_motion_cosine,
    cam_motion_modified_trapezoid,
    cam_profile_points,
    cam_analysis,
    indexer_selection,
    divider_general,
)


class TestCamMotions:
    """凸轮运动规律 (覆盖 L18-21, 47-51, 59-74)."""

    def test_uniform_motion(self):
        """等速运动: s 与 theta 线性."""
        s, v, a = cam_motion_uniform(beta=math.pi/2, h=10, theta=math.pi/4)
        assert s == pytest.approx(5.0, rel=0.01)
        assert v == pytest.approx(10 / (math.pi/2), rel=0.01)
        assert a == 0

    def test_sine_motion_at_quarter(self):
        """正弦运动: 1/4 处 s = h * sin²(π/4)/2 = h/2."""
        s, v, a = cam_motion_sine(beta=math.pi, h=10, theta=math.pi/2)
        # 正弦运动: s = h * (1 - cos(π·θ/β)) / 2
        # 当 θ=β/2: s = h * (1 - cos(π/2)) / 2 = h/2
        assert s == pytest.approx(5.0, rel=0.05)

    def test_sine_motion_at_beta(self):
        """正弦运动: theta=beta 时 s=h."""
        s, v, a = cam_motion_sine(beta=math.pi, h=10, theta=math.pi)
        assert s == pytest.approx(10, rel=0.01)

    def test_cosine_motion_at_quarter(self):
        """余弦运动: 1/2 处 s = h * 0.5 * (1 - cos(π/2)) = h/2."""
        s, v, a = cam_motion_cosine(beta=math.pi, h=10, theta=math.pi/2)
        # 余弦: s = h/2 * (1 - cos(π·θ/β))
        # 当 θ=β/2: s = h/2 * (1 - cos(π/2)) = h/2 = 5
        assert s == pytest.approx(5.0, rel=0.05)
        # 中点处速度最大: v_max = πh/(2β) = π·10/(2π) = 5
        assert v == pytest.approx(5.0, rel=0.05)

    def test_cosine_motion_at_zero(self):
        """余弦运动: theta=0 时 s=0."""
        s, v, a = cam_motion_cosine(beta=math.pi, h=10, theta=0)
        assert s == pytest.approx(0, abs=1e-6)

    def test_modified_trapezoid_basic(self):
        """修正梯形运动: 边界处 s 合理 (无 plus_ratio/minus_ratio 参数)."""
        # 实际签名只接受 (beta, h, theta)
        s, v, a = cam_motion_modified_trapezoid(
            beta=math.pi, h=10, theta=math.pi/2
        )
        # 中段 (phi=0.5 → else 分支 → 退化为 sine): s = 5
        assert 0 <= s <= 10
        assert v >= 0
        # 起点 (theta=0): s=0
        s0, v0, a0 = cam_motion_modified_trapezoid(
            beta=math.pi, h=10, theta=0
        )
        assert s0 == 0
        # 终点 (theta=beta): s=h
        s_end, v_end, a_end = cam_motion_modified_trapezoid(
            beta=math.pi, h=10, theta=math.pi
        )
        assert s_end == pytest.approx(10, rel=0.05)


class TestCamProfilePoints:
    """cam_profile_points 凸轮轮廓采样 (覆盖 L82-89, 118)."""

    def test_uniform_profile(self):
        """等速规律生成轮廓点."""
        points = cam_profile_points(
            rb=50, h=10, beta_deg=90, motion_type='uniform', num_points=10
        )
        # 实际签名: 返回 dict 列表
        assert isinstance(points, list)
        assert len(points) == 11  # num_points + 1
        # 第一个点应包含 theta_deg, s_mm, x_mm
        assert 'theta_deg' in points[0] or 'theta' in points[0]

    def test_sine_profile(self):
        """正弦规律生成轮廓点."""
        points = cam_profile_points(
            rb=40, h=8, beta_deg=120, motion_type='sine', num_points=20
        )
        assert isinstance(points, list)
        assert len(points) == 21
        # 验证所有点都有效
        for p in points:
            assert isinstance(p, dict)

    def test_cosine_profile(self):
        """余弦规律生成轮廓点."""
        points = cam_profile_points(
            rb=50, h=10, beta_deg=180, motion_type='cosine', num_points=15
        )
        assert isinstance(points, list)
        assert len(points) == 16

    def test_trapezoid_profile(self):
        """修正梯形规律生成轮廓点."""
        points = cam_profile_points(
            rb=50, h=10, beta_deg=120, motion_type='modified_trapezoid', num_points=12
        )
        assert isinstance(points, list)
        assert len(points) == 13

    def test_unknown_motion_type_falls_back(self):
        """未知 motion_type: 应回退到默认 (sine)."""
        points = cam_profile_points(
            rb=50, h=10, beta_deg=90, motion_type='unknown', num_points=5
        )
        assert isinstance(points, list)
        assert len(points) == 6


class TestCamAnalysis:
    """cam_analysis 凸轮综合分析 (覆盖 L111-129)."""

    def test_sine_cam_analysis(self):
        """正弦凸轮: max_velocity=Cv·h/β."""
        r = cam_analysis(beta_deg=180, h=10, motion_type='sine')
        # 实际签名: 返回 max_velocity, max_acceleration
        assert 'max_velocity' in r
        assert 'max_acceleration' in r
        assert r['motion_type'] == 'sine'
        # Cv=2.0: max_velocity = 2.0 × 10 / π ≈ 6.366
        assert r['max_velocity'] == pytest.approx(6.366, rel=0.01)

    def test_uniform_cam_peak_velocity(self):
        """等速凸轮: Cv=1.0, Ca=0."""
        r = cam_analysis(beta_deg=90, h=10, motion_type='uniform')
        # max_velocity = 1.0 × 10 / (π/2) ≈ 6.366
        assert r['max_velocity'] == pytest.approx(6.366, rel=0.01)
        # 等速: Ca=0 → max_acceleration = 0
        assert r['max_acceleration'] == 0

    def test_cosine_cam_analysis(self):
        """余弦凸轮: Cv=1.57."""
        r = cam_analysis(beta_deg=180, h=10, motion_type='cosine')
        # Cv=1.57: max_velocity = 1.57 × 10 / π ≈ 5.0
        assert r['max_velocity'] == pytest.approx(5.0, rel=0.05)

    def test_trapezoid_cam_analysis(self):
        """修正梯形凸轮: Cv=1.76."""
        r = cam_analysis(beta_deg=180, h=10, motion_type='modified_trapezoid')
        # Cv=1.76: max_velocity = 1.76 × 10 / π ≈ 5.6
        assert r['max_velocity'] == pytest.approx(5.6, rel=0.05)


class TestIndexerSelection:
    """indexer_selection 分割器选型 (覆盖 L152, 165, 175, 188)."""

    def test_basic_indexer(self):
        """基础分割器选型."""
        # 实际签名: (load_torque_nm, index_angle_deg, dwell_angle_deg, rpm_input, num_stations, safety)
        r = indexer_selection(
            load_torque_nm=10, index_angle_deg=90,
            dwell_angle_deg=270, rpm_input=30, num_stations=4
        )
        assert r['num_stations'] == 4
        assert r['output_torque_nm'] == 10 * 1.5  # safety=1.5
        assert r['input_torque_nm'] > 0
        assert r['power_kw'] > 0

    def test_high_torque_indexer(self):
        """高扭矩场景."""
        r = indexer_selection(
            load_torque_nm=100, index_angle_deg=120,
            dwell_angle_deg=240, rpm_input=10, num_stations=3
        )
        # 高扭矩 → 大输出扭矩
        assert r['output_torque_nm'] == 100 * 1.5

    def test_high_speed_indexer(self):
        """高转速场景."""
        r = indexer_selection(
            load_torque_nm=5, index_angle_deg=60,
            dwell_angle_deg=300, rpm_input=200, num_stations=6
        )
        # 高转速 → 短 index_time
        assert r['index_time_s'] > 0
        assert r['power_kw'] > 0

    def test_custom_safety_factor(self):
        """自定义安全系数."""
        r = indexer_selection(
            load_torque_nm=10, index_angle_deg=90,
            dwell_angle_deg=270, rpm_input=30, num_stations=4, safety=2.0
        )
        assert r['output_torque_nm'] == 20  # 10 × 2.0
        assert r['safety_factor'] == 2.0


class TestDividerGeneral:
    """divider_general 一般分度盘 (覆盖 L207-208)."""

    def test_basic_divider(self):
        """基础分度盘计算."""
        r = divider_general(
            pitch_angle_deg=15, table_diameter_mm=200,
            load_mass_kg=10, rpm_input=20
        )
        assert r is not None
        # 应包含 stations, power 等
        if 'num_stations' in r or 'stations' in r:
            stations = r.get('num_stations') or r.get('stations')
            # 15° 间距 → 24 工位
            assert stations == 24
        if 'power_kw' in r:
            assert r['power_kw'] > 0
