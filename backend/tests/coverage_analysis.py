"""分析覆盖率数据, 生成覆盖率提升计划.

输入: coverage_data.json
输出: 分类报告 (生产代码 vs 脚本 vs 测试)
"""
import json
from pathlib import Path

# 加载覆盖率数据
data = json.loads(Path("c:/Users/Administrator/机械计算小程序/coverage_data.json").read_text(encoding="utf-8"))
files = data["files"]

# 分类
PRODUCTION_PATTERNS = ["backend/api/", "backend/calculations/", "backend/database/",
                      "backend/data/", "backend/utils/", "backend/config.py",
                      "backend/app.py", "backend/calculations", "backend/database"]

SCRIPT_FILES = ["build_i18n", "extract_data", "smoke_test", "test_all.py"]
TEST_FILES_KEYWORDS = ["tests/", "verify_", "analyze_", "concurrent_", "manual_api"]

def classify(path):
    p = str(path).replace("\\", "/")
    for k in TEST_FILES_KEYWORDS + SCRIPT_FILES:
        if k in p:
            return "script_or_test"
    for k in PRODUCTION_PATTERNS:
        if p.startswith(k.replace("\\", "/")):
            return "production"
    return "other"

# 分类统计
groups = {"production": [], "script_or_test": []}
for fpath, fdata in files.items():
    cls = classify(fpath)
    if cls in groups:
        groups[cls].append((fpath, fdata))

print("=" * 100)
print("代码覆盖率分类分析")
print("=" * 100)

# 整体
total_stmts = sum(fd["summary"]["num_statements"] for _, fd in files.items())
total_miss = sum(fd["summary"]["missing_lines"] for _, fd in files.items())
print(f"\n整体: stmts={total_stmts}, miss={total_miss}, cover={100*(total_stmts-total_miss)/total_stmts:.1f}%")

# 生产代码
prod_stmts = sum(fd["summary"]["num_statements"] for _, fd in groups["production"])
prod_miss = sum(fd["summary"]["missing_lines"] for _, fd in groups["production"])
prod_cover = 100 * (prod_stmts - prod_miss) / prod_stmts if prod_stmts else 0
print(f"生产代码: stmts={prod_stmts}, miss={prod_miss}, cover={prod_cover:.1f}%")

# 脚本/测试
scr_stmts = sum(fd["summary"]["num_statements"] for _, fd in groups["script_or_test"])
scr_miss = sum(fd["summary"]["missing_lines"] for _, fd in groups["script_or_test"])
scr_cover = 100 * (scr_stmts - scr_miss) / scr_stmts if scr_stmts else 0
print(f"脚本/测试: stmts={scr_stmts}, miss={scr_miss}, cover={scr_cover:.1f}%")

# 生产代码低覆盖率模块 (按缺失行数排序)
print("\n" + "=" * 100)
print("生产代码低覆盖率模块 TOP 15 (按缺失行数)")
print("=" * 100)
print(f"  {'File':<50} {'Stmts':>6} {'Miss':>6} {'Cover':>8}  Missing Lines")
print("-" * 100)
for fpath, fd in sorted(groups["production"], key=lambda x: -x[1]["summary"]["missing_lines"]):
    s = fd["summary"]
    cover = 100 * (s["num_statements"] - s["missing_lines"]) / s["num_statements"] if s["num_statements"] else 0
    if s["missing_lines"] > 0 and cover < 100:
        miss_lines = s.get("missing_lines", 0)
        # 找具体未覆盖行
        missing_lines_detail = []
        for k, v in fd.items():
            if k.startswith("index") and v.get("missing_lines"):
                ml = v["missing_lines"]
                if ml:
                    # 转成实际行号
                    nums = []
                    cur = 0
                    for i, c in enumerate(v.get("context", {}).get("lines", [])):
                        pass
                    break
        # 简化显示
        miss_str = s.get("excluded_lines", "?")
        print(f"  {fpath:<50} {s['num_statements']:>6} {s['missing_lines']:>6} {cover:>7.1f}%")

# 计算目标: 提升至 80%
print("\n" + "=" * 100)
print("覆盖率目标计算 (生产代码)")
print("=" * 100)
target_cover = 80.0
target_miss = int(prod_stmts * (1 - target_cover / 100))
need_reduce = prod_miss - target_miss
print(f"  当前生产: {prod_stmts} stmts, {prod_miss} miss, {prod_cover:.1f}%")
print(f"  目标 80%: {target_miss} miss max")
print(f"  需减少:   {need_reduce} 行未覆盖")

# 优先级排序 (影响行数最多)
print("\n" + "=" * 100)
print("高优先级: 提升 ROI 最大的模块")
print("=" * 100)
priority_modules = []
for fpath, fd in sorted(groups["production"], key=lambda x: -x[1]["summary"]["missing_lines"]):
    s = fd["summary"]
    if s["missing_lines"] > 5:  # 大于 5 行的才考虑
        priority_modules.append((fpath, s))
        cover = 100 * (s["num_statements"] - s["missing_lines"]) / s["num_statements"]
        print(f"  • {fpath}  (miss={s['missing_lines']}, cover={cover:.1f}%)")

print(f"\n  优先级模块数: {len(priority_modules)}")
