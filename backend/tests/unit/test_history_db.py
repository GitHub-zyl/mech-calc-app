"""单元测试: database/history_db.py

覆盖 init_db / add / get / list / delete / count / stats / clear
"""
import json
import pytest
import time
from pathlib import Path

import backend.database.history_db as hdb


@pytest.fixture
def fresh_db(tmp_path: Path):
    """每次测试用临时数据库."""
    db_path = tmp_path / "test_history.db"
    hdb.init_db(db_path)
    hdb.clear_all()
    yield db_path
    # 清理
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass


# ============ init_db ============

def test_init_db_creates_file(tmp_path: Path):
    p = tmp_path / "x.db"
    result = hdb.init_db(p)
    assert result == p
    assert p.exists()


def test_init_db_idempotent(tmp_path: Path):
    p = tmp_path / "x.db"
    hdb.init_db(p)
    hdb.init_db(p)  # 多次调用应幂等
    assert p.exists()


# ============ add_record ============

def test_add_record_returns_id(fresh_db):
    rid = hdb.add_record(
        category='gear', endpoint='/api/calc/gear/spur',
        input_data={'m': 2, 'z': 20}, output_data={'d': 40}
    )
    assert isinstance(rid, int)
    assert rid > 0


def test_add_record_with_all_fields(fresh_db):
    rid = hdb.add_record(
        category='bearing', endpoint='/api/calc/bearing/life',
        input_data={'C': 15, 'P': 5}, output_data={'L10h': 5000},
        calc_id='bearing-life',
        client_ip='127.0.0.1',
        duration_ms=1.2,
        ts=1234567890.0,
    )
    rec = hdb.get_record(rid)
    assert rec['category'] == 'bearing'
    assert rec['calc_id'] == 'bearing-life'
    assert rec['client_ip'] == '127.0.0.1'
    assert rec['duration_ms'] == 1.2
    assert rec['ts'] == 1234567890.0
    assert rec['input'] == {'C': 15, 'P': 5}
    assert rec['output'] == {'L10h': 5000}


def test_add_record_missing_category(fresh_db):
    with pytest.raises(ValueError):
        hdb.add_record(
            category='', endpoint='/api/x',
            input_data={}, output_data={}
        )


def test_add_record_missing_endpoint(fresh_db):
    with pytest.raises(ValueError):
        hdb.add_record(
            category='x', endpoint='',
            input_data={}, output_data={}
        )


# ============ get_record ============

def test_get_record_not_found(fresh_db):
    assert hdb.get_record(99999) is None


def test_get_record_json_deserialization(fresh_db):
    """嵌套 dict 也能正常反序列化"""
    rid = hdb.add_record(
        category='x', endpoint='/x',
        input_data={'nested': {'a': [1, 2, 3]}},
        output_data={'list': [{'k': 'v'}]}
    )
    rec = hdb.get_record(rid)
    assert rec['input'] == {'nested': {'a': [1, 2, 3]}}
    assert rec['output'] == {'list': [{'k': 'v'}]}


# ============ list_records ============

def test_list_records_default(fresh_db):
    for i in range(3):
        hdb.add_record(
            category='gear', endpoint='/x',
            input_data={'i': i}, output_data={'o': i}
        )
    items = hdb.list_records()
    assert len(items) == 3
    # 倒序: 后插入的在前
    assert items[0]['input']['i'] == 2


def test_list_records_pagination(fresh_db):
    for i in range(10):
        hdb.add_record(
            category='x', endpoint='/x',
            input_data={'i': i}, output_data={}
        )
    items = hdb.list_records(limit=3, offset=0)
    assert len(items) == 3
    items2 = hdb.list_records(limit=3, offset=3)
    assert len(items2) == 3
    # 不同页 ID 不重叠
    ids1 = {it['id'] for it in items}
    ids2 = {it['id'] for it in items2}
    assert ids1.isdisjoint(ids2)


def test_list_records_filter_by_category(fresh_db):
    hdb.add_record(category='gear', endpoint='/x', input_data={}, output_data={})
    hdb.add_record(category='bearing', endpoint='/x', input_data={}, output_data={})
    hdb.add_record(category='gear', endpoint='/x', input_data={}, output_data={})
    items = hdb.list_records(category='gear')
    assert len(items) == 2
    assert all(it['category'] == 'gear' for it in items)


def test_list_records_filter_by_calc_id(fresh_db):
    hdb.add_record(category='x', endpoint='/x', input_data={}, output_data={}, calc_id='a')
    hdb.add_record(category='x', endpoint='/x', input_data={}, output_data={}, calc_id='b')
    items = hdb.list_records(calc_id='a')
    assert len(items) == 1


def test_list_records_filter_by_time(fresh_db):
    hdb.add_record(category='x', endpoint='/x', input_data={}, output_data={}, ts=1000)
    hdb.add_record(category='x', endpoint='/x', input_data={}, output_data={}, ts=2000)
    hdb.add_record(category='x', endpoint='/x', input_data={}, output_data={}, ts=3000)
    items = hdb.list_records(since=1500, until=2500)
    assert len(items) == 1
    assert items[0]['ts'] == 2000


# ============ delete_record ============

def test_delete_record_success(fresh_db):
    rid = hdb.add_record(category='x', endpoint='/x', input_data={}, output_data={})
    assert hdb.delete_record(rid) is True
    assert hdb.get_record(rid) is None


def test_delete_record_not_found(fresh_db):
    assert hdb.delete_record(99999) is False


def test_delete_records_batch(fresh_db):
    ids = [hdb.add_record(category='x', endpoint='/x', input_data={}, output_data={}) for _ in range(5)]
    n = hdb.delete_records(ids[:3])
    assert n == 3
    assert hdb.count_records() == 2


def test_delete_records_empty(fresh_db):
    n = hdb.delete_records([])
    assert n == 0


# ============ count / stats ============

def test_count_records(fresh_db):
    assert hdb.count_records() == 0
    hdb.add_record(category='a', endpoint='/x', input_data={}, output_data={})
    hdb.add_record(category='b', endpoint='/x', input_data={}, output_data={})
    hdb.add_record(category='a', endpoint='/x', input_data={}, output_data={})
    assert hdb.count_records() == 3
    assert hdb.count_records(category='a') == 2


def test_stats_by_category(fresh_db):
    hdb.add_record(category='a', endpoint='/x', input_data={}, output_data={})
    hdb.add_record(category='a', endpoint='/x', input_data={}, output_data={})
    hdb.add_record(category='b', endpoint='/x', input_data={}, output_data={})
    s = hdb.stats_by_category()
    assert s == {'a': 2, 'b': 1}


# ============ clear_all ============

def test_clear_all(fresh_db):
    for _ in range(5):
        hdb.add_record(category='x', endpoint='/x', input_data={}, output_data={})
    n = hdb.clear_all()
    assert n == 5
    assert hdb.count_records() == 0


# ============ get_db_path ============

def test_get_db_path(fresh_db):
    p = hdb.get_db_path()
    assert p is not None
    assert str(p).endswith('test_history.db')
