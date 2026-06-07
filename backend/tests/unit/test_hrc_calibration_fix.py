"""单元测试: backend/calculations/surface.py HRC 公式校准

任务: 修复 calc_hardness_convert 中 HRC 公式的 calibration 缺陷

参考: ASTM E140 / GB/T 1172-1999 硬度换算表
- HB 200 → HRC 13.5
- HB 250 → HRC 22.0
- HB 300 → HRC 29.8
- HB 350 → HRC 36.0
- HB 400 → HRC 41.5
- HB 450 → HRC 45.7
"""
import pytest

from backend.calculations.surface import calc_hardness_convert


class TestHrcFormulaCalibration:
    """HRC 公式 calibration 测试 (按 ASTM E140 / GB/T 1172)."""

    def test_hb200_to_hrc(self):
        """HB=200 → HRC ≈ 13.5 (而非被截断的 70)."""
        r = calc_hardness_convert(value=200, from_type='HB', to_type='HRC')
        v = r.get('value_converted')
        # 校准公式: HRC ≈ 0.143 × HB - 14.6
        # HB=200 → 0.143×200 - 14.6 = 14.0
        assert v is not None
        assert 12 <= v <= 16, f"HB=200 应得 HRC ≈ 14, 实际={v}"

    def test_hb250_to_hrc(self):
        """HB=250 → HRC ≈ 22.0."""
        r = calc_hardness_convert(value=250, from_type='HB', to_type='HRC')
        v = r.get('value_converted')
        assert v is not None
        assert 20 <= v <= 24, f"HB=250 应得 HRC ≈ 22, 实际={v}"

    def test_hb300_to_hrc(self):
        """HB=300 → HRC ≈ 29.8."""
        r = calc_hardness_convert(value=300, from_type='HB', to_type='HRC')
        v = r.get('value_converted')
        assert v is not None
        assert 28 <= v <= 32, f"HB=300 应得 HRC ≈ 30, 实际={v}"

    def test_hb350_to_hrc(self):
        """HB=350 → HRC ≈ 36.0."""
        r = calc_hardness_convert(value=350, from_type='HB', to_type='HRC')
        v = r.get('value_converted')
        assert v is not None
        assert 34 <= v <= 38, f"HB=350 应得 HRC ≈ 36, 实际={v}"

    def test_hb400_to_hrc(self):
        """HB=400 → HRC ≈ 41.5."""
        r = calc_hardness_convert(value=400, from_type='HB', to_type='HRC')
        v = r.get('value_converted')
        assert v is not None
        assert 40 <= v <= 44, f"HB=400 应得 HRC ≈ 42, 实际={v}"

    def test_hb100_to_300_range_monotonic(self):
        """HB 100-300 范围内 HRC 应单调递增, 且符合经验值."""
        prev = 0
        for hb in [100, 150, 180, 200, 220, 250, 280, 300]:
            r = calc_hardness_convert(value=hb, from_type='HB', to_type='HRC')
            v = r.get('value_converted')
            if v is not None and v > 0:
                # 单调性
                assert v >= prev, f"HB={hb} 转换值{v} 应 >= 上一值{prev}"
                # 范围合理性
                assert 0 <= v <= 70, f"HB={hb} 转换值{v} 越界"
            prev = v

    def test_hb_low_value_returns_below_range(self):
        """HB < 180 (低硬度): HRC 应低于 12 或返回 None (低于 HRC 量程)."""
        r = calc_hardness_convert(value=100, from_type='HB', to_type='HRC')
        v = r.get('value_converted')
        # HB=100 远低于 HRC 适用范围 (HRC 仅适用 20-70)
        # 校准后应返回 0 或很小值, 而非错误的 70
        assert v is None or v <= 12, f"HB=100 → HRC 应 ≤ 12, 实际={v}"

    def test_hb_high_value_capped_safely(self):
        """HB > 650 (高硬度): HRC 上限 70, 不会越界."""
        r = calc_hardness_convert(value=800, from_type='HB', to_type='HRC')
        v = r.get('value_converted')
        if v is not None:
            assert v <= 70, f"HB=800 → HRC 应 ≤ 70, 实际={v}"

    def test_hrc_to_hb_consistency(self):
        """HRC → HB 反向换算: 应与正向大致对偶."""
        # 先正向: HB=300 → HRC ≈ 30
        r1 = calc_hardness_convert(value=300, from_type='HB', to_type='HRC')
        hrc = r1.get('value_converted')
        if hrc and 20 <= hrc <= 50:
            # 再反向: HRC=30 → HB ≈ 300
            r2 = calc_hardness_convert(value=hrc, from_type='HRC', to_type='HB')
            hb_back = r2.get('value_converted')
            # 允许一定误差
            if hb_back is not None:
                assert 200 <= hb_back <= 400, f"HRC→HB 反向误差过大: {hrc} → {hb_back}"


class TestHrcFormulaDoesNotCapAt70:
    """回归测试: 验证 HB=200 不再被错误截断为 70."""

    def test_hb200_does_not_return_70(self):
        """HB=200 绝不能返回 70 (历史 bug)."""
        r = calc_hardness_convert(value=200, from_type='HB', to_type='HRC')
        v = r.get('value_converted')
        assert v != 70, "BUG 回归: HB=200 被错误截断为 HRC=70"
        assert v is not None and v < 30, f"HB=200 应得 HRC ≈ 14, 实际={v}"

    def test_hb250_does_not_return_70(self):
        """HB=250 绝不能返回 70."""
        r = calc_hardness_convert(value=250, from_type='HB', to_type='HRC')
        v = r.get('value_converted')
        assert v != 70, "BUG 回归: HB=250 被错误截断为 HRC=70"
        assert v is not None and v < 35, f"HB=250 应得 HRC ≈ 22, 实际={v}"
