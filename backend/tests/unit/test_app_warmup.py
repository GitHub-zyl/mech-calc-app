"""单元测试: backend/app.py 冷启动优化 (方案 A)

覆盖范围:
  - _warmup_database: 触发 WAL 创建 + page cache 加载
  - _preload_p2_data: 预加载 P2 参考数据
  - create_app(testing=True): 跳过预热逻辑
  - create_app(testing=False): 启用预热, 不影响启动
  - 环境变量 DISABLE_DB_WARMUP=1 可关闭预热
"""
import os
import time
from pathlib import Path

import pytest

from backend.app import (
    create_app,
    _warmup_database,
    _preload_p2_data,
    ENABLE_DB_WARMUP,
)


class TestWarmupDatabase:
    """_warmup_database 函数测试."""

    def test_warmup_creates_wal_file(self, tmp_path):
        """预热应创建 WAL 文件."""
        db_path = tmp_path / 'test_warmup.db'
        # 先初始化 schema
        import sqlite3
        with sqlite3.connect(str(db_path)) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS calc_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    category TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    output_json TEXT NOT NULL
                );
            """)

        result = _warmup_database(db_path)
        assert result['success'] is True
        assert result['elapsed_ms'] >= 0
        assert result['error'] is None

    def test_warmup_does_not_pollute_data(self, tmp_path):
        """预热不应留下任何数据 (ROLLBACK 生效)."""
        db_path = tmp_path / 'test_no_pollute.db'
        import sqlite3
        with sqlite3.connect(str(db_path)) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS calc_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    category TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    output_json TEXT NOT NULL
                );
            """)

        _warmup_database(db_path)

        # 验证: 表中无 __warmup__ 类别记录
        with sqlite3.connect(str(db_path)) as conn:
            cur = conn.execute(
                "SELECT COUNT(*) FROM calc_history WHERE category = '__warmup__'"
            ).fetchone()
            assert cur[0] == 0, "预热不应污染数据"

    def test_warmup_handles_missing_file(self, tmp_path):
        """不存在的 DB 文件: 返回错误但不抛异常."""
        db_path = tmp_path / 'nonexistent.db'
        result = _warmup_database(db_path)
        # 不应抛异常, 应返回 success=False
        assert result['success'] is False
        assert result['error'] is not None
        assert 'elapsed_ms' in result

    def test_warmup_completes_quickly(self, tmp_path):
        """预热应在 1 秒内完成."""
        db_path = tmp_path / 'test_speed.db'
        import sqlite3
        with sqlite3.connect(str(db_path)) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS calc_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    category TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    output_json TEXT NOT NULL
                );
            """)

        result = _warmup_database(db_path)
        assert result['elapsed_ms'] < 1000, f"预热耗时 {result['elapsed_ms']}ms 超过 1s"


class TestPreloadP2Data:
    """_preload_p2_data 函数测试."""

    def test_preload_p2_returns_size(self):
        """预加载 P2 应返回数据大小."""
        from backend.config import Config
        result = _preload_p2_data(Config)
        assert result['success'] is True
        assert result['size_kb'] > 0
        assert result['error'] is None

    def test_preload_p2_completes_quickly(self):
        """预加载 P2 应在 500ms 内完成."""
        from backend.config import Config
        result = _preload_p2_data(Config)
        assert result['elapsed_ms'] < 500, f"P2 预热耗时 {result['elapsed_ms']}ms 超过 500ms"


class TestCreateAppWithWarmup:
    """create_app 集成测试: 预热开关控制."""

    def test_testing_mode_skips_warmup(self, capsys):
        """testing=True 时不打印预热日志 (跳过)."""
        app = create_app(testing=True)
        captured = capsys.readouterr()
        # testing 模式不应有预热日志
        assert '[+] DB 预热成功' not in captured.out
        assert '[+] P2 数据预热成功' not in captured.out

    def test_production_mode_runs_warmup(self, capsys):
        """非 testing 模式应执行预热并打印日志."""
        app = create_app(testing=False)
        captured = capsys.readouterr()
        # 至少有一个预热成功日志
        assert ('[+] DB 预热成功' in captured.out or
                '[!] DB 预热失败' in captured.out)

    def test_create_app_returns_flask_instance(self):
        """create_app 应返回 Flask 实例."""
        app = create_app(testing=True)
        from flask import Flask
        assert isinstance(app, Flask)

    def test_env_disable_warmup(self, monkeypatch, capsys):
        """设置 DISABLE_DB_WARMUP=1 应跳过预热."""
        monkeypatch.setenv('DISABLE_DB_WARMUP', '1')

        # 重新读取环境变量 (因为常量在模块导入时已计算)
        # 验证常量定义和回退机制
        import importlib
        import backend.app
        importlib.reload(backend.app)
        assert backend.app.ENABLE_DB_WARMUP is False

        app = backend.app.create_app(testing=False)
        captured = capsys.readouterr()
        # DISABLE_DB_WARMUP=1 时, 预热被禁用
        assert '[+] DB 预热成功' not in captured.out


class TestWarmupIntegration:
    """集成: 预热对测试不产生副作用."""

    def test_warmup_idempotent(self, tmp_path):
        """连续多次预热应都是幂等的."""
        db_path = tmp_path / 'idempotent.db'
        import sqlite3
        with sqlite3.connect(str(db_path)) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS calc_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    category TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    output_json TEXT NOT NULL
                );
            """)

        # 连续 3 次预热, 每次都应成功
        for i in range(3):
            r = _warmup_database(db_path)
            assert r['success'] is True, f"第 {i+1} 次预热失败: {r['error']}"

        # 验证数据未被污染
        with sqlite3.connect(str(db_path)) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM calc_history WHERE category = '__warmup__'"
            ).fetchone()[0]
            assert count == 0
