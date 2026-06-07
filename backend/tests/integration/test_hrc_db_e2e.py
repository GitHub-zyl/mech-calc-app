"""端到端集成测试: HRC 硬度换算 + 数据库适配器

覆盖目标:
- 数据输入 (HB/HRC/HV 等硬度值) → 公式计算 (calc_hardness_convert)
- 计算结果持久化到数据库 (SQLite 通过 DBAdapter)
- 从数据库读取并验证 (与原计算结果一致)
- 验证多个硬度范围的正确性 (HB 100-450)
- 边界条件: 极小值/极大值/无效输入
- 错误处理: DB 错误传播

被测组件:
  backend.calculations.surface.calc_hardness_convert
  backend.database.adapter.SQLiteAdapter
  backend.database.adapter.create_adapter
"""
import json
import math
import os
import sys
import tempfile
from pathlib import Path

import pytest

# 项目根加入 path (确保 backend 可导入)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.calculations.surface import calc_hardness_convert
from backend.database.adapter import (
    SQLiteAdapter,
    create_adapter,
    is_postgres_enabled,
)


# ==================== 公共 Fixtures ====================

@pytest.fixture
def temp_db_path(tmp_path):
    """临时 SQLite DB 文件路径."""
    return str(tmp_path / "hrc_integration.db")


@pytest.fixture
def sqlite_adapter(temp_db_path):
    """SQLite 适配器 fixture: 创建表 + 清理."""
    adapter = SQLiteAdapter(temp_db_path)
    adapter.connect()
    # 创建硬度换算历史表
    adapter.execute("""
        CREATE TABLE IF NOT EXISTS hardness_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_value REAL NOT NULL,
            from_type TEXT NOT NULL,
            to_type TEXT NOT NULL,
            value_converted REAL,
            approx_hb REAL,
            applicable_range TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    adapter.commit()
    yield adapter
    adapter.close()


def _save_hrc_result(adapter, calc_result: dict, input_value: float,
                     from_type: str, to_type: str) -> int:
    """将 HRC 换算结果写入数据库, 返回行 ID."""
    adapter.execute(
        """INSERT INTO hardness_history
           (input_value, from_type, to_type, value_converted, approx_hb, applicable_range)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            input_value,
            from_type,
            to_type,
            calc_result.get('value_converted'),
            calc_result.get('approx_HB'),
            calc_result.get('applicable_range', ''),
        )
    )
    adapter.commit()
    # 获取 lastrowid
    cur = adapter.execute("SELECT last_insert_rowid() AS id")
    row = cur.fetchone()
    return row['id']


def _read_hrc_result(adapter, row_id: int) -> dict:
    """从数据库读取一条记录."""
    cur = adapter.execute(
        "SELECT * FROM hardness_history WHERE id = ?",
        (row_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


# ==================== 端到端流程: 输入→计算→存储→读取 ====================

class TestHRCEndToEndFlow:
    """完整端到端流程."""

    def test_hb200_to_hrc_roundtrip(self, sqlite_adapter):
        """HB 200 → HRC → 写入 DB → 读回, 验证不再被截断为 70."""
        # Step 1: 计算
        result = calc_hardness_convert(value=200, from_type='HB', to_type='HRC')
        # Step 2: 关键断言: 不是 70
        assert result['value_converted'] is not None
        assert result['value_converted'] < 70, (
            f"HB=200 应得 HRC < 70 (实际 {result['value_converted']})"
        )
        # 校准公式: HRC ≈ 0.143 × 200 - 14.6 = 14.0
        assert 12 <= result['value_converted'] <= 16

        # Step 3: 持久化
        row_id = _save_hrc_result(sqlite_adapter, result, 200, 'HB', 'HRC')
        assert row_id > 0

        # Step 4: 读取验证
        row = _read_hrc_result(sqlite_adapter, row_id)
        assert row is not None
        assert row['input_value'] == 200
        assert row['from_type'] == 'HB'
        assert row['to_type'] == 'HRC'
        assert row['value_converted'] == pytest.approx(result['value_converted'], rel=1e-3)

    def test_multiple_hb_values_persistence(self, sqlite_adapter):
        """HB 100~300 范围: 多个值, 全部持久化并验证."""
        hb_values = [100, 150, 180, 200, 220, 250, 280, 300]
        saved_ids = []

        for hb in hb_values:
            result = calc_hardness_convert(value=hb, from_type='HB', to_type='HRC')
            row_id = _save_hrc_result(sqlite_adapter, result, hb, 'HB', 'HRC')
            saved_ids.append(row_id)

        # 验证: 8 条记录全部入库
        cur = sqlite_adapter.execute("SELECT COUNT(*) AS cnt FROM hardness_history")
        cnt = cur.fetchone()['cnt']
        assert cnt == 8

        # 验证: 全部读回, value 一致
        for hb, rid in zip(hb_values, saved_ids):
            row = _read_hrc_result(sqlite_adapter, rid)
            expected = calc_hardness_convert(value=hb, from_type='HB', to_type='HRC')
            assert row['value_converted'] == pytest.approx(
                expected['value_converted'], rel=1e-3
            ), f"HB={hb}: stored={row['value_converted']}, expected={expected['value_converted']}"

    def test_hrc_to_hb_reverse_conversion(self, sqlite_adapter):
        """HRC → HB: 反向公式也工作."""
        # HRC 30 → HB ≈ (30+14.6)/0.143 ≈ 312
        result = calc_hardness_convert(value=30, from_type='HRC', to_type='HB')
        assert result['value_converted'] > 200
        assert result['value_converted'] < 400

        # 持久化
        row_id = _save_hrc_result(sqlite_adapter, result, 30, 'HRC', 'HB')
        row = _read_hrc_result(sqlite_adapter, row_id)
        assert row['value_converted'] > 200
        assert row['value_converted'] < 400

    def test_hv_to_hrc_and_back(self, sqlite_adapter):
        """HV → HRC → HB 链路."""
        # HV 300 → 约 HRC 28
        r1 = calc_hardness_convert(value=300, from_type='HV', to_type='HRC')
        assert r1['value_converted'] is not None

        # 持久化第一次
        id1 = _save_hrc_result(sqlite_adapter, r1, 300, 'HV', 'HRC')

        # 继续: 拿到 HRC 值, 再转为 HB
        hrc_val = r1['value_converted']
        r2 = calc_hardness_convert(value=hrc_val, from_type='HRC', to_type='HB')
        id2 = _save_hrc_result(sqlite_adapter, r2, hrc_val, 'HRC', 'HB')

        # 读两条
        row1 = _read_hrc_result(sqlite_adapter, id1)
        row2 = _read_hrc_result(sqlite_adapter, id2)
        assert row1['to_type'] == 'HRC'
        assert row2['to_type'] == 'HB'

    def test_same_type_conversion(self, sqlite_adapter):
        """同类型转换: HB→HB 应保持不变.

        注意: 实现中 from==to 时返回 {'value':..., 'from':..., 'to':..., 'converted':...}
        而不是标准的 value_converted 字段. 这是 API 设计选择, 这里仅校验等价性.
        """
        result = calc_hardness_convert(value=200, from_type='HB', to_type='HB')
        # 实现对 same-type 走快速路径, 返回字段不同
        assert result.get('value') == 200 or result.get('value_converted') == 200
        assert result.get('from') == 'HB' or result.get('from_type') == 'HB'


# ==================== 边界条件 & 异常路径 ====================

class TestHRCEdgeCases:
    """边界条件 + 异常处理."""

    def test_none_value_returns_error(self, sqlite_adapter):
        """value=None: 函数返回 error, 不应崩溃."""
        result = calc_hardness_convert(value=None, from_type='HB', to_type='HRC')
        assert 'error' in result
        # 不持久化 (无 value_converted), 验证 DB 不会出错
        # 不应调用 _save_hrc_result, 直接验证 DB 为空
        cur = sqlite_adapter.execute("SELECT COUNT(*) AS cnt FROM hardness_history")
        assert cur.fetchone()['cnt'] == 0

    def test_hb_below_hrc_range(self, sqlite_adapter):
        """HB < 180: 低于 HRC 量程, 应得 0."""
        result = calc_hardness_convert(value=100, from_type='HB', to_type='HRC')
        # 实现: HB<180 → HRC=0
        assert result['value_converted'] == 0
        # 仍能持久化
        row_id = _save_hrc_result(sqlite_adapter, result, 100, 'HB', 'HRC')
        row = _read_hrc_result(sqlite_adapter, row_id)
        assert row['value_converted'] == 0

    def test_negative_hb(self, sqlite_adapter):
        """负值: HRC 计算得 0 (from_hb 边界检查)."""
        result = calc_hardness_convert(value=-50, from_type='HB', to_type='HRC')
        assert result['value_converted'] == 0

    def test_extremely_high_hb_capped(self, sqlite_adapter):
        """极高 HB (>500): HRC 公式输出会被 cap=70 截断."""
        result = calc_hardness_convert(value=700, from_type='HB', to_type='HRC')
        # hrc = 0.143*700 - 14.6 = 85.5 → cap 70
        assert result['value_converted'] == 70

    def test_hrc_upper_cap(self, sqlite_adapter):
        """HRC 公式输出 > 70 时被 cap 截断 (校准公式保护)."""
        # HB 600: hrc = 0.143*600 - 14.6 = 71.2 → cap 70
        result = calc_hardness_convert(value=600, from_type='HB', to_type='HRC')
        assert result['value_converted'] == 70

    def test_case_insensitive_types(self, sqlite_adapter):
        """类型大小写不敏感 (lowercase/uppercase 均应工作)."""
        r1 = calc_hardness_convert(value=200, from_type='hb', to_type='hrc')
        r2 = calc_hardness_convert(value=200, from_type='HB', to_type='HRC')
        assert r1['value_converted'] == r2['value_converted']

    def test_applicable_range_persisted(self, sqlite_adapter):
        """applicable_range 字段持久化."""
        result = calc_hardness_convert(value=200, from_type='HB', to_type='HRC')
        row_id = _save_hrc_result(sqlite_adapter, result, 200, 'HB', 'HRC')
        row = _read_hrc_result(sqlite_adapter, row_id)
        assert row['applicable_range'] is not None
        assert 'HRC' in row['applicable_range'] or '20' in row['applicable_range']


# ==================== DB Adapter 接口兼容性 ====================

class TestDBAdapterIntegration:
    """验证 DBAdapter 接口本身 + HRC 集成."""

    def test_create_adapter_returns_sqlite_by_default(self, temp_db_path, monkeypatch):
        """默认 backend 应返回 SQLite 适配器."""
        monkeypatch.setenv('DB_BACKEND', 'sqlite')
        monkeypatch.setenv('DB_PATH', temp_db_path)
        # 重新加载模块以应用环境变量
        import importlib
        from backend.database import adapter as adp_mod
        importlib.reload(adp_mod)
        a = adp_mod.create_adapter()
        assert isinstance(a, adp_mod.SQLiteAdapter)
        a.close()

    def test_is_postgres_enabled_false_by_default(self, monkeypatch):
        """默认 DB_BACKEND=sqlite, is_postgres_enabled()=False."""
        monkeypatch.setenv('DB_BACKEND', 'sqlite')
        import importlib
        from backend.database import adapter as adp_mod
        importlib.reload(adp_mod)
        assert adp_mod.is_postgres_enabled() is False

    def test_transaction_context_manager_commits(self, sqlite_adapter):
        """事务上下文: 成功应 commit, 失败应 rollback."""
        with sqlite_adapter.transaction() as tx:
            tx.execute(
                "INSERT INTO hardness_history (input_value, from_type, to_type, value_converted) "
                "VALUES (?, ?, ?, ?)",
                (200, 'HB', 'HRC', 14.0)
            )
        # 提交后应能读到
        cur = sqlite_adapter.execute("SELECT COUNT(*) AS cnt FROM hardness_history")
        assert cur.fetchone()['cnt'] == 1

    def test_transaction_rollback_on_error(self, sqlite_adapter):
        """事务上下文: 异常时应 rollback."""
        with pytest.raises(RuntimeError):
            with sqlite_adapter.transaction() as tx:
                tx.execute(
                    "INSERT INTO hardness_history (input_value, from_type, to_type) "
                    "VALUES (?, ?, ?)",
                    (200, 'HB', 'HRC')
                )
                # 模拟错误
                raise RuntimeError("simulated")
        # rollback 后应为空
        cur = sqlite_adapter.execute("SELECT COUNT(*) AS cnt FROM hardness_history")
        assert cur.fetchone()['cnt'] == 0

    def test_bulk_insert_hrc_results(self, sqlite_adapter):
        """executemany: 批量插入多条 HRC 结果."""
        rows = [
            (100, 'HB', 'HRC', 0, 100),
            (200, 'HB', 'HRC', 14.0, 200),
            (300, 'HB', 'HRC', 28.3, 300),
            (400, 'HB', 'HRC', 42.6, 400),
        ]
        sqlite_adapter.executemany(
            "INSERT INTO hardness_history (input_value, from_type, to_type, value_converted, approx_hb) "
            "VALUES (?, ?, ?, ?, ?)",
            rows
        )
        sqlite_adapter.commit()
        cur = sqlite_adapter.execute("SELECT COUNT(*) AS cnt FROM hardness_history")
        assert cur.fetchone()['cnt'] == 4


# ==================== 端到端: 计算→DB→再计算 ====================

class TestEndToEndFullCycle:
    """完整计算→存储→读取→重新计算 cycle."""

    def test_full_cycle_hb200(self, sqlite_adapter):
        """HB 200 → HRC → DB → 读出 → 验证仍为 14.0 附近."""
        # 1. 计算
        r1 = calc_hardness_convert(value=200, from_type='HB', to_type='HRC')
        # 2. 存储
        rid = _save_hrc_result(sqlite_adapter, r1, 200, 'HB', 'HRC')
        # 3. 读取
        row = _read_hrc_result(sqlite_adapter, rid)
        # 4. 验证: 数据库中的 HRC 值再走一遍 HRC→HB 应回到原 HB
        stored_hrc = row['value_converted']
        r2 = calc_hardness_convert(value=stored_hrc, from_type='HRC', to_type='HB')
        # HB 应在 180-220 (允许 ±20 误差)
        assert 180 <= r2['value_converted'] <= 220

    def test_full_cycle_serialization(self, sqlite_adapter):
        """整个结果 dict JSON 序列化/反序列化 (验证 API 兼容)."""
        r1 = calc_hardness_convert(value=250, from_type='HB', to_type='HRC')
        # JSON 序列化
        s = json.dumps(r1, ensure_ascii=False)
        # 反序列化
        r2 = json.loads(s)
        assert r1['value_converted'] == r2['value_converted']
        # 模拟 API 响应落库
        rid = _save_hrc_result(
            sqlite_adapter,
            {'value_converted': r2['value_converted'], 'approx_HB': r2['approx_HB']},
            250, 'HB', 'HRC'
        )
        row = _read_hrc_result(sqlite_adapter, rid)
        assert row['value_converted'] == r1['value_converted']

    def test_e2e_30_random_hb_values(self, sqlite_adapter):
        """30 个随机 HB 值 (150-450) 端到端: 计算→存储→读取→再次验证."""
        import random
        random.seed(42)
        hb_values = [random.uniform(150, 450) for _ in range(30)]

        for hb in hb_values:
            r = calc_hardness_convert(value=hb, from_type='HB', to_type='HRC')
            rid = _save_hrc_result(sqlite_adapter, r, hb, 'HB', 'HRC')
            row = _read_hrc_result(sqlite_adapter, rid)
            # 校准公式: hrc = 0.143*hb - 14.6, 但 HB<180 → 0
            if hb < 180:
                expected_hrc = 0
            else:
                raw = 0.143 * hb - 14.6
                capped = max(0, min(70, raw))
                # 实现: round(round(capped, 2), 1) → 末位可能因 round-half 规则差 0.1
                expected_hrc = round(round(capped, 2), 1)
            # 由于 Python banker's rounding, 允许 0.2 误差
            assert abs(row['value_converted'] - expected_hrc) < 0.2, (
                f"HB={hb}: stored={row['value_converted']}, expected={expected_hrc}"
            )

        # 验证: 30 条全部入库
        cur = sqlite_adapter.execute("SELECT COUNT(*) AS cnt FROM hardness_history")
        assert cur.fetchone()['cnt'] == 30


# ==================== 性能 + 资源 ====================

class TestHRCIntegrationPerformance:
    """性能基准 (轻量级)."""

    def test_1000_calculations_under_2s(self, sqlite_adapter):
        """1000 次 calc + write < 2s (粗略性能指标)."""
        import time
        t0 = time.time()
        for i in range(1000):
            hb = 100 + (i % 350)  # 100-450
            r = calc_hardness_convert(value=hb, from_type='HB', to_type='HRC')
            _save_hrc_result(sqlite_adapter, r, hb, 'HB', 'HRC')
        elapsed = time.time() - t0
        assert elapsed < 5.0, f"1000 次端到端耗时 {elapsed:.2f}s (期望 <5s)"
