"""机械设计常用计算表 — 启动脚本"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from app import app
import sys
enc = sys.stdout.encoding
if enc and enc.upper() in ('GBK', 'GB2312', 'CP936'):
    title = 'Mech Design Calculator v2.0'
    start = 'Start: http://127.0.0.1:9091'
    stop = 'Press Ctrl+C to stop'
else:
    title = '\u2699 \u673a\u68b0\u8bbe\u8ba1\u5e38\u7528\u8ba1\u7b97\u8868 v2.0'
    start = '\u542f\u52a8: http://127.0.0.1:9090'
    stop = '\u6309 Ctrl+C \u505c\u6b62'
print('=' * 50)
print(title)
print('=' * 50)
print(start)
print(stop)
print('=' * 50)
app.run(host='127.0.0.1', port=9091)
