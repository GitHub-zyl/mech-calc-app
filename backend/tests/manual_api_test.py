"""手动 API 测试脚本 - /api/history 和 /api/formulas
运行: python -m backend.tests.manual_api_test
"""
import json
import sys
import os

# 强制 UTF-8 输出 (Windows GBK 环境)
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import time
from datetime import datetime

BASE = "http://127.0.0.1:9091"

def timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def log(msg):
    try:
        print(f"[{timestamp()}] {msg}", flush=True)
    except UnicodeEncodeError:
        # GBK 环境下, 替换为安全字符
        safe = msg.encode('gbk', errors='replace').decode('gbk', errors='replace')
        print(f"[{timestamp()}] {safe}", flush=True)

def safe_get_json(r):
    try:
        return r.json()
    except Exception:
        return None

def test_history():
    log("=" * 70)
    log("Task 2-A: /api/history 接口测试")
    log("=" * 70)
    import requests
    results = []

    # 1. 健康 (stats)
    log("\n[1] GET /api/history/stats")
    r = requests.get(f"{BASE}/api/history/stats")
    log(f"    Status: {r.status_code}")
    log(f"    Response: {json.dumps(r.json(), ensure_ascii=False, indent=2)}")
    results.append(("stats", r.status_code == 200))

    # 2. 清理后重新插入
    requests.delete(f"{BASE}/api/history?all=1")
    log("\n[2] 清理后 GET /api/history (应为空)")
    r = requests.get(f"{BASE}/api/history")
    j = r.json()
    log(f"    Status: {r.status_code}, total={j['data']['pagination']['total']}, items={len(j['data']['items'])}")
    results.append(("list_empty", j['data']['pagination']['total'] == 0))

    # 3. POST 成功
    log("\n[3] POST /api/history 正常插入")
    body = {
        "category": "manual_test", "endpoint": "/api/manual/test",
        "calc_id": "manual-1",
        "input": {"param1": 10, "param2": "value"},
        "output": {"result": 42},
        "duration_ms": 1.23,
    }
    r = requests.post(f"{BASE}/api/history", json=body)
    log(f"    Status: {r.status_code}")
    j = r.json()
    log(f"    Response keys: {list(j.keys())}")
    log(f"    data.record keys: {list(j['data']['record'].keys())}")
    rid = j['data']['id']
    log(f"    id={rid}, category={j['data']['record']['category']}, duration_ms={j['data']['record']['duration_ms']}")
    results.append(("post_ok", r.status_code == 200 and j['status'] == 'ok'))

    # 4. 批量插入
    log("\n[4] 批量插入 5 条")
    for i in range(5):
        requests.post(f"{BASE}/api/history", json={
            "category": f"cat_{i % 2}", "endpoint": f"/api/x/{i}",
            "input": {"i": i}, "output": {},
        })
    r = requests.get(f"{BASE}/api/history")
    j = r.json()
    log(f"    Status: {r.status_code}, total={j['data']['pagination']['total']}")
    results.append(("bulk_insert", j['data']['pagination']['total'] == 6))

    # 5. 列表分页
    log("\n[5] GET /api/history?limit=2&offset=0 (分页)")
    r = requests.get(f"{BASE}/api/history?limit=2&offset=0")
    j = r.json()
    log(f"    items={len(j['data']['items'])}, has_more={j['data']['pagination']['has_more']}")
    log(f"    pagination: {j['data']['pagination']}")
    results.append(("pagination", len(j['data']['items']) == 2))

    # 6. 分类筛选
    log("\n[6] GET /api/history?category=cat_0 (分类筛选)")
    r = requests.get(f"{BASE}/api/history?category=cat_0")
    items = r.json()['data']['items']
    cats = {it['category'] for it in items}
    log(f"    items={len(items)}, unique_cats={cats}")
    results.append(("filter_category", cats == {'cat_0'}))

    # 7. 详情
    log("\n[7] GET /api/history/<id> 详情")
    r = requests.get(f"{BASE}/api/history/{rid}")
    log(f"    Status: {r.status_code}")
    log(f"    input: {r.json()['data']['input']}")
    log(f"    client_ip: {r.json()['data']['client_ip']}")
    results.append(("detail", r.status_code == 200))

    # 8. 错误路径 - 缺 category
    log("\n[8] POST 缺 category (期望 400)")
    r = requests.post(f"{BASE}/api/history", json={"endpoint": "/x", "input": {}, "output": {}})
    log(f"    Status: {r.status_code}, message: {r.json()['message']}")
    results.append(("err_missing_category", r.status_code == 400))

    # 9. 错误路径 - 不存在 id
    log("\n[9] GET /api/history/999999 (期望 404)")
    r = requests.get(f"{BASE}/api/history/999999")
    log(f"    Status: {r.status_code}, message: {r.json()['message']}")
    results.append(("err_not_found", r.status_code == 404))

    # 10. 错误路径 - limit 非整数
    log("\n[10] GET /api/history?limit=abc (期望 400)")
    r = requests.get(f"{BASE}/api/history?limit=abc")
    log(f"    Status: {r.status_code}, message: {r.json()['message']}")
    results.append(("err_invalid_limit", r.status_code == 400))

    # 11. DELETE 单条
    log("\n[11] DELETE /api/history/<id> 单条删除")
    r = requests.delete(f"{BASE}/api/history/{rid}")
    log(f"    Status: {r.status_code}, data: {r.json()['data']}")
    results.append(("delete_single", r.status_code == 200))

    # 12. DELETE 批量
    log("\n[12] DELETE /api/history?all=1 清空")
    r = requests.delete(f"{BASE}/api/history?all=1")
    log(f"    Status: {r.status_code}, cleared: {r.json()['data']['cleared']}")
    results.append(("delete_all", r.status_code == 200))

    # 13. categories
    log("\n[13] GET /api/history/categories")
    r = requests.get(f"{BASE}/api/history/categories")
    log(f"    Status: {r.status_code}, data: {r.json()['data']}")
    results.append(("categories", r.status_code == 200))

    # 14. 中文 input/output
    log("\n[14] POST 中文 input/output (Unicode)")
    r = requests.post(f"{BASE}/api/history", json={
        "category": "材料", "endpoint": "/x",
        "input": {"材料": "Q235", "厚度": "2mm"},
        "output": {"结论": "OK"},
    })
    rid_cn = r.json()['data']['id']
    rec = requests.get(f"{BASE}/api/history/{rid_cn}").json()['data']
    log(f"    Status: {r.status_code}")
    log(f"    input: {rec['input']}")
    log(f"    output: {rec['output']}")
    results.append(("unicode", rec['input']['材料'] == 'Q235'))

    # 清理
    requests.delete(f"{BASE}/api/history?all=1")

    return results


def test_formulas():
    log("=" * 70)
    log("Task 2-B: /api/formulas 接口测试")
    log("=" * 70)
    import requests
    results = []

    # 1. 列表
    log("\n[1] GET /api/formulas (列表)")
    r = requests.get(f"{BASE}/api/formulas")
    j = r.json()
    log(f"    Status: {r.status_code}")
    log(f"    total={j['data']['total']}, q={j['data']['q']!r}, category={j['data']['category']!r}")
    log(f"    items[0]: id={j['data']['items'][0]['id']}, name_zh={j['data']['items'][0]['name_zh']}")
    results.append(("list", r.status_code == 200 and j['data']['total'] >= 20))

    # 2. 分类
    log("\n[2] GET /api/formulas/categories")
    r = requests.get(f"{BASE}/api/formulas/categories")
    log(f"    Status: {r.status_code}, data: {r.json()['data']}")
    results.append(("categories", r.status_code == 200))

    # 3. 按 id 搜索
    log("\n[3] GET /api/formulas?q=fma")
    r = requests.get(f"{BASE}/api/formulas?q=fma")
    items = r.json()['data']['items']
    log(f"    Status: {r.status_code}, hits={len(items)}, ids={[it['id'] for it in items]}")
    results.append(("search_id", any(it['id'] == 'fma' for it in items)))

    # 4. 按中文名搜索
    log("\n[4] GET /api/formulas?q=牛顿 (中文名搜索)")
    r = requests.get(f"{BASE}/api/formulas?q=牛顿")
    items = r.json()['data']['items']
    log(f"    Status: {r.status_code}, hits={len(items)}")
    for it in items:
        log(f"      - {it['id']} | {it['name_zh']}")
    results.append(("search_zh", any(it['id'] == 'fma' for it in items)))

    # 5. 按英文名搜索
    log("\n[5] GET /api/formulas?q=Bernoulli (英文名搜索)")
    r = requests.get(f"{BASE}/api/formulas?q=Bernoulli")
    items = r.json()['data']['items']
    log(f"    Status: {r.status_code}, hits={len(items)}, ids={[it['id'] for it in items]}")
    results.append(("search_en", any(it['id'] == 'bernoulli' for it in items)))

    # 6. 按分类筛选
    log("\n[6] GET /api/formulas?category=geometry")
    r = requests.get(f"{BASE}/api/formulas?category=geometry")
    items = r.json()['data']['items']
    log(f"    Status: {r.status_code}, hits={len(items)}")
    log(f"    all geometry: {all(it['category'] == 'geometry' for it in items)}")
    results.append(("filter_category", all(it['category'] == 'geometry' for it in items)))

    # 7. 组合筛选
    log("\n[7] GET /api/formulas?q=圆&category=geometry")
    r = requests.get(f"{BASE}/api/formulas?q=圆&category=geometry")
    items = r.json()['data']['items']
    log(f"    Status: {r.status_code}, hits={len(items)}")
    results.append(("combined", len(items) >= 1 and all(it['category'] == 'geometry' for it in items)))

    # 8. 详情
    log("\n[8] GET /api/formulas/fma 详情")
    r = requests.get(f"{BASE}/api/formulas/fma")
    j = r.json()
    f = j['data']
    log(f"    Status: {r.status_code}")
    log(f"    id={f['id']}, name_zh={f['name_zh']}, formula={f['formula']}")
    log(f"    variables: {f['variables']}")
    log(f"    category={f['category']}, tags={f['tags']}")
    results.append(("detail", r.status_code == 200 and f['id'] == 'fma'))

    # 9. 相关
    log("\n[9] GET /api/formulas/fma/related")
    r = requests.get(f"{BASE}/api/formulas/fma/related")
    j = r.json()
    related = j['data']['related']
    log(f"    Status: {r.status_code}")
    log(f"    related count: {len(related)}")
    for r_item in related:
        log(f"      - {r_item['id']} | {r_item['name_zh']}")
    results.append(("related", r.status_code == 200 and len(related) >= 1))

    # 10. 求解 - F=ma 求 F
    log("\n[10] POST /api/formulas/fma/solve 求 F (m=10, a=2)")
    r = requests.post(f"{BASE}/api/formulas/fma/solve", json={"given": {"m": 10, "a": 2}})
    j = r.json()['data']
    log(f"    Status: {r.status_code}")
    log(f"    target={j['target']}, value={j['value']}, unit={j['unit']}")
    log(f"    formula: {j['formula']}")
    log(f"    result: {j['result']}")
    results.append(("solve_ok", abs(j['value'] - 20) < 1e-9))

    # 11. 求解 - 使用默认值
    log("\n[11] POST /api/formulas/pfg/solve 求 G (m=10, g=默认值 9.81)")
    r = requests.post(f"{BASE}/api/formulas/pfg/solve", json={"given": {"m": 10}})
    j = r.json()['data']
    log(f"    Status: {r.status_code}")
    log(f"    target={j['target']}, value={j['value']}")
    results.append(("solve_default", abs(j['value'] - 98.1) < 1e-6))

    # 12. 求解 - 已知量不足
    log("\n[12] POST /api/formulas/fma/solve 缺量 (只有 m)")
    r = requests.post(f"{BASE}/api/formulas/fma/solve", json={"given": {"m": 10}})
    log(f"    Status: {r.status_code}")
    log(f"    message: {r.json()['message']}")
    log(f"    details: {r.json()['details']}")
    results.append(("solve_missing", r.status_code == 400))

    # 13. 求解 - 公式不存在
    log("\n[13] POST /api/formulas/xxx_yyy/solve (公式不存在)")
    r = requests.post(f"{BASE}/api/formulas/xxx_yyy/solve", json={"given": {"a": 1}})
    log(f"    Status: {r.status_code}, message: {r.json()['message']}")
    results.append(("solve_not_found", r.status_code == 404))

    # 14. 求解 - given 类型错误
    log("\n[14] POST /api/formulas/fma/solve given 非 dict")
    r = requests.post(f"{BASE}/api/formulas/fma/solve", json={"given": "not a dict"})
    log(f"    Status: {r.status_code}, message: {r.json()['message']}")
    results.append(("solve_bad_type", r.status_code == 400))

    # 15. 求解 - 数值无效
    log("\n[15] POST /api/formulas/fma/solve given 含非数字字符串")
    r = requests.post(f"{BASE}/api/formulas/fma/solve", json={"given": {"m": "abc", "a": 2}})
    log(f"    Status: {r.status_code}, message: {r.json()['message']}")
    results.append(("solve_bad_value", r.status_code == 400))

    # 16. 响应格式一致性
    log("\n[16] 所有响应格式一致性 (status=ok + data)")
    for url in ['/api/formulas', '/api/formulas/fma', '/api/formulas/categories', '/api/formulas/fma/related']:
        r = requests.get(f"{BASE}{url}")
        j = r.json()
        ok = j['status'] == 'ok' and 'data' in j
        log(f"    {url:35s} -> status={j['status']:6s} has_data={'data' in j}")
        if not ok:
            results.append((f"shape_{url}", False))
    results.append(("shape_consistent", True))

    return results


def main():
    log(f"Base URL: {BASE}")
    log(f"Start time: {datetime.now().isoformat()}\n")

    history_results = test_history()
    formulas_results = test_formulas()

    log("\n" + "=" * 70)
    log("测试结果汇总")
    log("=" * 70)

    log("\n--- /api/history ---")
    for name, ok in history_results:
        log(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    log("\n--- /api/formulas ---")
    for name, ok in formulas_results:
        log(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    total = len(history_results) + len(formulas_results)
    passed = sum(1 for _, ok in history_results + formulas_results if ok)
    log(f"\n  Total: {passed}/{total} 通过 ({passed/total*100:.1f}%)")

    log(f"\nEnd time: {datetime.now().isoformat()}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
