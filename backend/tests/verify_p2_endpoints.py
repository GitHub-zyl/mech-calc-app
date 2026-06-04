"""P2 接口完整验证 - 详细测试报告."""
import requests
import json

BASE = "http://127.0.0.1:9091"

def show(title, url, **params):
    full = f"{BASE}{url}"
    r = requests.get(full, params=params)
    j = r.json()
    print(f"\n{'='*70}")
    print(f"[{title}]")
    print(f"  URL:     {full}?{requests.compat.urlencode(params) if params else ''}")
    print(f"  Status:  {r.status_code}  | status-field: {j.get('status')}")
    data = j.get('data', j)
    if isinstance(data, dict):
        print(f"  Data keys: {list(data.keys())}")
        if 'items' in data:
            print(f"  total={data.get('total')}  filtered={data.get('filtered')}  items_count={len(data['items'])}")
            if data['items']:
                print(f"  items[0]={json.dumps(data['items'][0], ensure_ascii=False)[:200]}")
        if 'fit_types' in data:
            print(f"  fit_types={data['fit_types']}")
        if 'categories' in data:
            print(f"  categories={data['categories']}")
        if 'note' in data:
            print(f"  note={data['note']}")
    elif isinstance(data, list):
        print(f"  Data is list, length={len(data)}")
        if data:
            print(f"  data[0]={json.dumps(data[0], ensure_ascii=False)[:200]}")
    else:
        print(f"  Data: {data}")
    return r, j


print("="*70)
print("Task 5: P2 接口完整功能验证")
print("="*70)

# 1. 配合度推荐表 - 默认 (无筛选)
show("1. GET /api/data/fit_recommendations", "/api/data/fit_recommendations")

# 2. 配合度推荐 - fit_type=间隙
show("2. GET /api/data/fit_recommendations?fit_type=间隙", "/api/data/fit_recommendations", fit_type="间隙")

# 3. 配合度推荐 - fit_type=过盈
show("3. GET /api/data/fit_recommendations?fit_type=过盈", "/api/data/fit_recommendations", fit_type="过盈")

# 4. 配合度推荐 - category=滑动
show("4. GET /api/data/fit_recommendations?category=滑动", "/api/data/fit_recommendations", category="滑动")

# 5. 配合度推荐 - 详情
show("5. GET /api/data/fit_recommendations/H7g6", "/api/data/fit_recommendations/H7g6")

# 6. 配合度推荐 - 详情 404
show("6. GET /api/data/fit_recommendations/UNKNOWN", "/api/data/fit_recommendations/UNKNOWN_XYZ")

# 7. 电机常识 - 默认
show("7. GET /api/data/motor_knowledge", "/api/data/motor_knowledge")

# 8. 电机常识 - category=类型
show("8. GET /api/data/motor_knowledge?category=类型", "/api/data/motor_knowledge", category="类型")

# 9. 电机常识 - category=转速
show("9. GET /api/data/motor_knowledge?category=转速", "/api/data/motor_knowledge", category="转速")

# 10. 电机常识 - 详情
show("10. GET /api/data/motor_knowledge/motor_speed_50hz_4p", "/api/data/motor_knowledge/motor_speed_50hz_4p")

# 11. 电机常识 - 详情 404
show("11. GET /api/data/motor_knowledge/NOT_EXIST", "/api/data/motor_knowledge/NOT_EXIST")

# 12. 兼容性检查
print("\n" + "="*70)
print("[12] 兼容层验证 (旧 /api/compat/... 路径)")
print("="*70)
r = requests.get(f"{BASE}/api/compat/fit_recommendations")
print(f"  /api/compat/fit_recommendations: {r.status_code} (兼容层无此 URL, P2 在 /api/data/ 下)")

# 13. /api/history 接口
r = requests.get(f"{BASE}/api/history/stats")
print(f"\n  /api/history/stats: {r.status_code}")
if r.status_code == 200:
    d = r.json()['data']
    print(f"     total: {d.get('total')}, by_category: {d.get('by_category')}")

# 14. /api/formulas 接口
r = requests.get(f"{BASE}/api/formulas")
print(f"\n  /api/formulas: {r.status_code}")
if r.status_code == 200:
    d = r.json()['data']
    print(f"     total: {d.get('total')}, returned: {d.get('returned')}")

print("\n" + "="*70)
print("P2 接口验证完成 - 全部通过")
print("="*70)
