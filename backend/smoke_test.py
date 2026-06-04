"""冒烟测试: 验证 /modern 路由和 API 端点可达性"""
from backend.app import create_app
app = create_app(testing=True)
c = app.test_client()
r = c.get('/modern')
print(f'/modern -> {r.status_code}, {len(r.data)} bytes')
r = c.get('/api/meta/categories')
print(f'/api/meta/categories -> {r.status_code}')
j = r.get_json()
print(f'  categories: {len(j["data"])}')
print('  ids:', [c['id'] for c in j['data']])

# 计算端点冒烟
endpoints = [
    ('/api/calc/gear/spur', {'module': 2, 'teeth': 20}),
    ('/api/calc/tolerance/fit', {'nominal_mm': 50, 'hole_spec': 'H7', 'shaft_spec': 'g6'}),
    ('/api/calc/bearing/life', {'C_kN': 15, 'P_kN': 5, 'n_rpm': 1450}),
    ('/api/calc/pneumatic/force', {'pressure_mpa': 0.6, 'bore_mm': 80}),
    ('/api/calc/spring/compression', {'wire_diameter': 4, 'mean_diameter': 30, 'coils': 10}),
    ('/api/calc/hydraulic/pipe-pressure-loss', {'flow_lpm': 60, 'inner_diam_mm': 20, 'length_m': 5}),
    ('/api/calc/press/blanking', {'perimeter_mm': 100, 'thickness_mm': 2, 'shear_strength_mpa': 300}),
    ('/api/calc/brake/disc', {'T_Nm': 200, 'outer_radius_mm': 200, 'inner_radius_mm': 100, 'pressure_mpa': 0.5}),
    ('/api/calc/coupling/select', {'T_Nm': 200, 'n_rpm': 1450}),
]
for url, payload in endpoints:
    r = c.post(url, json=payload)
    j = r.get_json()
    print(f'  POST {url:50s} -> {r.status_code} status={j.get("status")}')

# ============ P0: /api/history 冒烟 ============
print('\n--- /api/history ---')

# 1. 健康 (stats)
r = c.get('/api/history/stats')
print(f'GET /api/history/stats -> {r.status_code}, total={r.get_json()["data"]["total"]}')

# 2. 新增记录
r = c.post('/api/history', json={
    'category': 'gear', 'endpoint': '/api/calc/gear/spur',
    'input': {'module': 2, 'teeth': 20}, 'output': {'d': 40},
    'duration_ms': 0.8,
})
assert r.status_code == 200, r.get_json()
rid = r.get_json()['data']['id']
print(f'POST /api/history -> 200, id={rid}')

# 3. 列表
r = c.get('/api/history?limit=5')
data = r.get_json()['data']
print(f'GET /api/history -> {r.status_code}, items={len(data["items"])}, total={data["pagination"]["total"]}')

# 4. 详情
r = c.get(f'/api/history/{rid}')
print(f'GET /api/history/{rid} -> {r.status_code}')

# 5. 错误路径
r = c.post('/api/history', json={'category': '', 'endpoint': '/x', 'input': {}, 'output': {}})
print(f'POST 缺 category -> {r.status_code} (期望 400)')
r = c.get('/api/history/999999')
print(f'GET 不存在 id -> {r.status_code} (期望 404)')

# 6. 清理测试数据
r = c.delete('/api/history?all=1')
print(f'DELETE 清空 -> {r.status_code}, cleared={r.get_json()["data"]["cleared"]}')

# ============ P1: /api/formulas 冒烟 ============
print('\n--- /api/formulas ---')

# 1. 列表
r = c.get('/api/formulas')
data = r.get_json()['data']
print(f'GET /api/formulas -> {r.status_code}, total={data["total"]}')

# 2. 分类
r = c.get('/api/formulas/categories')
cats = r.get_json()['data']
print(f'GET /api/formulas/categories -> {r.status_code}, cats={len(cats)}')

# 3. 搜索
r = c.get('/api/formulas?q=牛顿')
items = r.get_json()['data']['items']
print(f'GET q=牛顿 -> {r.status_code}, hits={len(items)} (期望含 fma)')

# 4. 详情
r = c.get('/api/formulas/fma')
print(f'GET /api/formulas/fma -> {r.status_code}, name={r.get_json()["data"]["name_zh"]}')

# 5. 相关
r = c.get('/api/formulas/fma/related')
related = r.get_json()['data']['related']
print(f'GET /api/formulas/fma/related -> {r.status_code}, related={len(related)}')

# 6. 求解
r = c.post('/api/formulas/fma/solve', json={'given': {'m': 10, 'a': 2}})
data = r.get_json()['data']
print(f'POST fma/solve m=10,a=2 -> {r.status_code}, F={data["value"]} N')

# 7. 错误路径
r = c.post('/api/formulas/fma/solve', json={'given': {'m': 10}})  # 缺 2 个
print(f'POST 缺量 -> {r.status_code} (期望 400)')
r = c.post('/api/formulas/xxx/solve', json={'given': {'a': 1}})  # 公式不存在
print(f'POST 不存在公式 -> {r.status_code} (期望 404)')

print('\n[smoke] 全部端点冒烟通过')
