"""验证日志输出"""
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] [%(threadName)s(tid=%(thread)d)] %(message)s'
)

from backend.calculations.formulas_data import solve, search
import requests

print('\n=== 测试1: 求解 F=ma ===')
r = solve('fma', {'m': 10, 'a': 2})
print(f'Result: {r}')

print('\n=== 测试2: 求解缺量 ===')
r = solve('fma', {'m': 10})
print(f'Result: {r}')

print('\n=== 测试3: 搜索 ===')
r = search('圆')
print(f'Result ids: {[f["id"] for f in r]}')

print('\n=== 测试4: 写入 history (通过 requests) ===')
for i in range(3):
    r = requests.post('http://127.0.0.1:9091/api/history', json={
        'category': f'cat_{i}', 'endpoint': f'/x/{i}',
        'input': {'i': i}, 'output': {'r': i*2},
    })
    print(f'  Status: {r.status_code}, id: {r.json()["data"]["id"]}')

print('\n=== 测试5: 删除 ===')
r = requests.delete('http://127.0.0.1:9091/api/history?all=1')
print(f'  Status: {r.status_code}, cleared: {r.json()["data"]["cleared"]}')
