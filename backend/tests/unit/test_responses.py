"""响应包装器单元测试"""
import pytest
from flask import Flask
from backend.api.responses import success, error


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


def test_success_default(app):
    with app.test_request_context():
        r = success({'value': 1})
        assert r.status_code == 200
        assert r.get_json() == {'status': 'ok', 'data': {'value': 1}}


def test_success_with_meta(app):
    with app.test_request_context():
        r = success({'a': 1}, meta={'count': 10})
        j = r.get_json()
        assert j['status'] == 'ok'
        assert j['data'] == {'a': 1}
        assert j['meta'] == {'count': 10}


def test_success_with_list_data(app):
    with app.test_request_context():
        r = success([1, 2, 3])
        j = r.get_json()
        assert j['data'] == [1, 2, 3]


def test_error_returns_400(app):
    with app.test_request_context():
        r = error('参数错误', code=400, details={'field': 'm'})
        assert r.status_code == 400
        j = r.get_json()
        assert j['status'] == 'error'
        assert j['message'] == '参数错误'
        assert j['code'] == 400
        assert j['details'] == {'field': 'm'}


def test_error_without_details(app):
    with app.test_request_context():
        r = error('not found', code=404)
        j = r.get_json()
        assert j['status'] == 'error'
        assert j['code'] == 404
        assert 'details' not in j


# ---- 同步测试 convert 工具 ----
from backend.utils.convert import safe_float, safe_int


def test_safe_float_normal():
    assert safe_float('3.14') == 3.14
    assert safe_float(42) == 42.0


def test_safe_float_invalid():
    assert safe_float('abc') is None
    assert safe_float('abc', 0.0) == 0.0
    assert safe_float(None) is None
    assert safe_float('') is None
    assert safe_float('', -1.0) == -1.0


def test_safe_int_normal():
    assert safe_int('10') == 10
    assert safe_int(3.7) == 3  # 截断
    assert safe_int('0x10') is None  # 16 进制不支持
