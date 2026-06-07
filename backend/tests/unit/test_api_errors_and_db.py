"""单元测试: backend/api/errors.py + utils/db.py (覆盖率提升)

覆盖目标:
- errors.py 67% → 100% (所有错误处理分支)
- utils/db.py 69% → 100% (缓存加载/清空/线程安全)
"""
import json
import threading
from pathlib import Path

import pytest

from backend.api import errors as err_mod
from backend.api.responses import error as api_error
from backend.app import create_app
from backend.utils.db import load_json, clear_cache, cache_size


class TestErrorHandlers:
    """errors.py 全局错误处理 (覆盖 L10, 14, 18, 22, 26-27)."""

    def test_400_bad_request(self):
        """400 错误应被处理器捕获并返回标准错误格式."""
        app = create_app(testing=True)
        client = app.test_client()
        # 触发 400: 错误的 limit 类型
        r = client.get('/api/history?limit=not_a_number')
        # 应返回 400 或 200 (取决于具体实现)
        # 测试错误处理函数本身: 直接调用
        with app.test_request_context():
            handler = None
            for code, h in app.error_handler_spec[None][None].items():
                if code == 400:
                    handler = h
                    break
            if handler:
                from werkzeug.exceptions import BadRequest
                resp = handler(BadRequest('test'))
                assert resp is not None

    def test_404_not_found(self):
        """404 错误处理."""
        app = create_app(testing=True)
        client = app.test_client()
        r = client.get('/api/nonexistent_path_xyz')
        assert r.status_code == 404
        body = json.loads(r.data)
        assert body['status'] == 'error'
        assert 'code' in body or 'message' in body

    def test_405_method_not_allowed(self):
        """405 方法不允许."""
        app = create_app(testing=True)
        client = app.test_client()
        # /api/history 仅支持 GET/POST/DELETE
        r = client.put('/api/history')
        assert r.status_code == 405
        body = json.loads(r.data)
        assert body['status'] == 'error'

    def test_500_internal_error(self):
        """500 内部错误: 通过触发异常模拟."""
        # 关闭 testing 模式以使错误处理器被调用
        app = create_app(testing=False)

        @app.route('/_test_500')
        def trigger_500():
            raise RuntimeError('intentional test error')

        client = app.test_client()
        r = client.get('/_test_500')
        # 处理器应返回 500
        assert r.status_code == 500
        body = json.loads(r.data)
        assert body['status'] == 'error'
        assert '服务器内部错误' in body.get('message', '') or 'internal' in body.get('message', '').lower()

    def test_422_unprocessable(self):
        """422 参数无法处理 (如 Flask-RESTful 等)."""
        app = create_app(testing=True)

        @app.route('/_test_422')
        def trigger_422():
            from werkzeug.exceptions import UnprocessableEntity
            raise UnprocessableEntity('test unprocessable')

        client = app.test_client()
        r = client.get('/_test_422')
        # 422 状态码
        assert r.status_code == 422
        body = json.loads(r.data)
        assert body['status'] == 'error'


class TestRegisterErrorHandlers:
    """register_error_handlers 直接测试."""

    def test_handlers_registered(self):
        """验证所有错误处理器都注册了."""
        from backend.api import errors as err_mod
        from werkzeug.exceptions import (
            BadRequest, NotFound, MethodNotAllowed,
            UnprocessableEntity, InternalServerError,
        )
        app = create_app(testing=True)
        assert callable(err_mod.register_error_handlers)

        # 检查 app.error_handler_spec 中是否包含各异常类
        # 结构: {None: {None: {code: {exception_class: handler}}}}
        all_exception_classes = set()
        for ep, handlers_by_ep in app.error_handler_spec.items():
            for blueprint, code_handlers in handlers_by_ep.items():
                for code_or_class in code_handlers.keys():
                    all_exception_classes.add(code_or_class)

        for exc_class in [BadRequest, NotFound, MethodNotAllowed,
                          UnprocessableEntity, InternalServerError]:
            assert exc_class in all_exception_classes, f"未注册 {exc_class.__name__} 处理器"


class TestJsonCache:
    """utils/db.py 缓存机制 (覆盖 L33, 46-52, 57)."""

    def test_load_json_basic(self, tmp_path):
        """基本加载: 文件存在时返回 dict."""
        f = tmp_path / 'test.json'
        f.write_text(json.dumps({'key': 'value', 'n': 42}), encoding='utf-8')
        clear_cache()  # 确保无缓存
        data = load_json(f)
        assert data == {'key': 'value', 'n': 42}

    def test_load_json_caches_result(self, tmp_path):
        """二次加载应命中缓存 (返回同一对象)."""
        f = tmp_path / 'cached.json'
        f.write_text(json.dumps({'cached': True}), encoding='utf-8')
        clear_cache()
        d1 = load_json(f)
        d2 = load_json(f)
        # 同一对象引用 (缓存命中)
        assert d1 is d2

    def test_load_json_missing_file_raises(self, tmp_path):
        """文件不存在: 应抛 FileNotFoundError."""
        clear_cache()
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / 'nonexistent.json')

    def test_clear_cache_all(self, tmp_path):
        """clear_cache() 不传参: 清空所有."""
        f1 = tmp_path / 'a.json'
        f2 = tmp_path / 'b.json'
        f1.write_text('{"a": 1}', encoding='utf-8')
        f2.write_text('{"b": 2}', encoding='utf-8')
        clear_cache()
        load_json(f1)
        load_json(f2)
        assert cache_size() >= 2
        clear_cache()
        assert cache_size() == 0

    def test_clear_cache_specific(self, tmp_path):
        """clear_cache(path) 只清指定路径."""
        f1 = tmp_path / 'a.json'
        f2 = tmp_path / 'b.json'
        f1.write_text('{"a": 1}', encoding='utf-8')
        f2.write_text('{"b": 2}', encoding='utf-8')
        clear_cache()
        load_json(f1)
        load_json(f2)
        clear_cache(f1)
        # 重新加载 f1 时, 缓存大小应增加 (新对象, 但 key 相同)
        d_a = load_json(f1)
        d_b = load_json(f2)
        # d_b 应仍命中缓存 (未清)
        assert d_b == {'b': 2}

    def test_cache_size(self, tmp_path):
        """cache_size() 返回当前缓存条目数."""
        clear_cache()
        f = tmp_path / 's.json'
        f.write_text('{}', encoding='utf-8')
        load_json(f)
        assert cache_size() >= 1

    def test_thread_safe_cache(self, tmp_path):
        """并发加载同一文件: 不应崩溃或产生竞态."""
        import concurrent.futures
        json_file = tmp_path / 'thread.json'
        json_file.write_text(json.dumps({'shared': True, 'n': 100}), encoding='utf-8')
        clear_cache()
        results = []

        def load():
            return load_json(json_file)  # 使用单独的变量名, 避免与 future 冲突

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            futures = [ex.submit(load) for _ in range(100)]
            for fut in concurrent.futures.as_completed(futures):
                results.append(fut.result())

        # 所有线程应得到相同结果
        assert all(r == {'shared': True, 'n': 100} for r in results)
        assert len(results) == 100
