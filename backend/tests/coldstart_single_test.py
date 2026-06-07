"""冷启动对比测试: 严格控制条件下对比 baseline vs optimized"""
import requests
import time
import uuid
import statistics
import json


def test_cold_start(label: str, run_count: int = 3) -> dict:
    """单次完整冷启动测试 (first + follow)."""
    results = {'first_ms': [], 'follow_ms': []}

    for run in range(run_count):
        # 首次请求 (冷启动)
        payload = {
            'category': f'coldstart_{label}',
            'endpoint': '/api/coldstart/single',
            'calc_id': f'coldstart-{label}-{uuid.uuid4().hex[:8]}',
            'input': {'ts': time.time(), 'run': run},
            'output': {'result': 'ok'},
            'duration_ms': 0.5,
        }
        start = time.perf_counter()
        r = requests.post('http://127.0.0.1:9091/api/history',
                          json=payload, timeout=10)
        first_ms = (time.perf_counter() - start) * 1000
        results['first_ms'].append(first_ms)

        # 5 次后续请求
        follow_durations = []
        for i in range(5):
            payload['calc_id'] = f'coldstart-{label}-{uuid.uuid4().hex[:8]}-{i}'
            start = time.perf_counter()
            r = requests.post('http://127.0.0.1:9091/api/history',
                              json=payload, timeout=10)
            follow_durations.append((time.perf_counter() - start) * 1000)
        results['follow_ms'].append(statistics.mean(follow_durations))

        print(f'  Run {run + 1}/{run_count}: first={first_ms:.2f}ms, '
              f'follow_avg={results["follow_ms"][-1]:.2f}ms, '
              f'ratio={first_ms / results["follow_ms"][-1]:.2f}x')

        # 清理本次数据
        items = requests.get('http://127.0.0.1:9091/api/history?limit=200',
                             timeout=5).json()['data']['items']
        ids = [it['id'] for it in items
               if (it.get('calc_id') or '').startswith(f'coldstart-{label}-')]
        if ids:
            requests.delete(f'http://127.0.0.1:9091/api/history?ids={",".join(map(str, ids))}',
                            timeout=5)

    first_avg = statistics.mean(results['first_ms'])
    follow_avg = statistics.mean(results['follow_ms'])
    return {
        'label': label,
        'runs': run_count,
        'first_avg_ms': round(first_avg, 3),
        'first_min_ms': round(min(results['first_ms']), 3),
        'first_max_ms': round(max(results['first_ms']), 3),
        'follow_avg_ms': round(follow_avg, 3),
        'cold_start_ratio': round(first_avg / follow_avg, 3) if follow_avg > 0 else 0,
    }


if __name__ == '__main__':
    import sys
    label = sys.argv[1] if len(sys.argv) > 1 else 'optimized'
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(f'=== 冷启动对比测试 [{label}] ({runs} 轮) ===')
    print()
    result = test_cold_start(label, runs)
    print()
    print(f'汇总 [{label}]:')
    print(f'  首次请求 avg:  {result["first_avg_ms"]}ms '
          f'(min={result["first_min_ms"]}, max={result["first_max_ms"]})')
    print(f'  后续请求 avg:  {result["follow_avg_ms"]}ms')
    print(f'  冷启动比例:    {result["cold_start_ratio"]}x')

    # 写到 JSON 文件
    output_path = f'coldstart_compare_{label}.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'  报告:          {output_path}')
