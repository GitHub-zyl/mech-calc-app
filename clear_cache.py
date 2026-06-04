"""清空 __pycache__"""
import shutil
import os
import sys

root = sys.argv[1] if len(sys.argv) > 1 else 'backend'
count = 0
for r, ds, fs in os.walk(root):
    for d in ds:
        if d == '__pycache__':
            full = os.path.join(r, d)
            try:
                shutil.rmtree(full, ignore_errors=False)
                count += 1
                print(f'removed: {full}')
            except Exception as e:
                print(f'failed: {full} -> {e}')
print(f'done, removed {count} dirs')
