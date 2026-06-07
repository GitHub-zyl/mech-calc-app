"""冷启动效应: 真实冷启动对比测试

方法:
- 完全清空 history.db, 停止服务
- 等 30 秒让 OS 释放 page cache
- 启动服务 (启用/禁用预热)
- 立即发 30 个请求, 分组分析:
  - 极冷 (前 5): 服务刚启动, 资源完全未加载
  - 温 (6-10): 索引/page cache 加载
  - 热 (11-30): 完全预热
- 对比两种模式下极冷 vs 热的延迟比例
"""
import requests
import time
import uuid
import statistics
import json
import sys


def test_cold_start_30(label: str) -> dict:
    """30 个连续请求的冷启动分析."""
    durations = []

    for i in range(30):
        payload = {
            'category': f'cold30_{label}',
            'endpoint': '/api/coldstart/30req',
            'calc_id': f'cold30-{label}-{uuid.uuid4().hex[:8]}-{i}',
            'input': {'ts': time.time(), 'i': i},
            'output': {'result': 'ok'},
            'duration_ms': 0.5,
        }
        start = time.perf_counter()
        r = requests.post('http://127.0.0.1:9091/api/history',
                          json=payload, timeout=10)
        durations.append((time.perf_counter() - start) * 1000)

    # 极冷 (1-5) vs 温 (6-10) vs 热 (11-30)
    very_cold = durations[0:5]
    warm = durations[5:10]
    hot = durations[10:30]

    print(f'\n  === {label} ===')
    print(f'  极冷 (1-5):   {statistics.mean(very_cold):.2f}ms (min={min(very_cold):.2f}, max={max(very_cold):.2f})')
    print(f'  温   (6-10):  {statistics.mean(warm):.2f}ms (min={min(warm):.2f}, max={max(warm):.2f})')
    print(f'  热   (11-30): {statistics.mean(hot):.2f}ms (min={min(hot):.2f}, max={max(hot):.2f})')
    print(f'  冷启动比例 (极冷/热): {statistics.mean(very_cold) / statistics.mean(hot):.2f}x')

    # 清理
    items = requests.get('http://127.0.0.1:9091/api/history?limit=200',
                         timeout=5).json()['data']['items']
    ids = [it['id'] for it in items
           if (it.get('calc_id') or '').startswith(f'cold30-{label}-')]
    if ids:
        requests.delete(f'http://127.0.0.1:9091/api/history?ids={",".join(map(str, ids))}',
                        timeout=5)

    return {
        'label': label,
        'very_cold_avg_ms': round(statistics.mean(very_cold), 3),
        'warm_avg_ms': round(statistics.mean(warm), 3),
        'hot_avg_ms': round(statistics.mean(hot), 3),
        'cold_start_ratio': round(statistics.mean(very_cold) / statistics.mean(hot), 3),
        'durations_ms': [round(d, 3) for d in durations],
    }


if __name__ == '__main__':
    label = sys.argv[1] if len(sys.argv) > 1 else 'optimized'

    print(f'=== 30 请求冷启动分析 [{label}] ===')
    result = test_cold_start_30(label)

    output_path = f'coldstart_30req_{label}.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'\n  报告: {output_path}')
