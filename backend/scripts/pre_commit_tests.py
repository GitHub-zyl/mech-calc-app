"""
Pre-Commit 自动化测试脚本
==========================

功能:
    1. 自动执行 HRC 公式修复验证测试 (test_hrc_hb200_standard.py)
    2. 自动执行 Tolerance 配合计算单元测试 (test_calculations_tolerance.py)
    3. 自动执行 H7 过渡配合本地测试 (test_h7_transition_fits.py)
    4. 生成详细测试报告 (文本/Markdown/JSON)
    5. 任何测试失败 → 退出码非 0 → git commit 被阻断

使用:
    # 手动运行
    python backend/scripts/pre_commit_tests.py

    # 配合 git pre-commit hook
    .git/hooks/pre-commit → 调用本脚本

退出码:
    0  - 全部通过, 允许 commit
    1  - 存在测试失败, 阻断 commit
    2  - 测试执行环境异常 (pytest 未安装等)
    3  - 用户中断 (Ctrl+C)
"""
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# ============================================================
# 路径与配置
# ============================================================
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

# 测试套件定义:
#   - pytest  类型:  pytest 收集并执行
#   - python  类型:  作为独立脚本执行, 通过退出码判断成败
TEST_SUITES = [
    {
        "name": "HRC 公式 (HB=200 修复点)",
        "path": "tests/integration/test_hrc_hb200_standard.py",
        "description": "验证 HRC 公式在 HB=200 时符合 ASTM E140 标准, 防止回退到 70 错误实现",
        "block_on_fail": True,
        "runner": "pytest",
        "category": "integration",
    },
    {
        "name": "Tolerance 配合计算 + 日志",
        "path": "tests/unit/test_calculations_tolerance.py",
        "description": "验证 fit_calculation 配合判别逻辑 + 优化后日志格式",
        "block_on_fail": True,
        "runner": "pytest",
        "category": "unit",
    },
    {
        "name": "H7/k6/H7/m6/H7/n6 过渡配合本地测试",
        "path": "tests/test_h7_transition_fits.py",
        "description": "H7/k6、H7/m6、H7/n6 配合类型本地端到端测试 + 报告生成",
        "block_on_fail": True,
        "runner": "python",  # 独立脚本
        "category": "integration",
    },
]

# 报告输出目录
REPORT_DIR = PROJECT_ROOT / "docs" / "coverage" / "pre_commit"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 辅助函数
# ============================================================
def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _format_duration(seconds: float) -> str:
    if seconds < 1.0:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        m, s = divmod(seconds, 60)
        return f"{int(m)}m{s:.0f}s"


def _parse_pytest_output(output: str, returncode: int) -> dict:
    """
    从 pytest 输出解析:
      - 通过/失败/跳过/错误数
      - 总耗时
      - 失败用例列表

    兼容多种 pytest 摘要格式:
      - "============================== 30 passed in 0.38s =============================="
      - "===== 5 failed, 10 passed, 2 skipped in 1.23s ====="
      - "1 failed, 2 errors in 0.50s"
    """
    import re

    result = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "duration_sec": 0.0,
        "failure_details": [],
    }

    # 1. 解析摘要行: 提取 "N passed" "N failed" "N skipped" "N error(s)" 和 "in X.XXs"
    for line in output.splitlines():
        # 仅匹配 pytest 摘要行 (含 in X.XXs 时间)
        m = re.search(r'\bin\s+([\d.]+)s', line)
        if m:
            try:
                result["duration_sec"] = float(m.group(1))
            except (ValueError, IndexError):
                pass

        # 提取数字+关键字组合 (数字必须在关键字前)
        for key, pattern in [
            ("passed", r'(\d+)\s+passed'),  # noqa: E241
            ("failed", r'(\d+)\s+failed'),  # noqa: E241
            ("skipped", r'(\d+)\s+skipped'),  # noqa: E241
            ("errors", r'(\d+)\s+errors?'),  # noqa: E241
        ]:
            m = re.search(pattern, line)
            if m:
                # 取最后一个匹配值, 避免被其他数字干扰
                result[key] = int(m.group(1))

    result["total"] = (
        result["passed"] + result["failed"]
        + result["skipped"] + result["errors"]  # noqa: W503
    )

    # 2. 提取失败详情
    if result["failed"] > 0 or result["errors"] > 0:
        in_failure = False
        current_failure = None
        for line in output.splitlines():
            stripped = line.strip()
            # 失败用例头: FAILED tests/...::test_xxx - ErrorType: message
            if stripped.startswith("FAILED ") or stripped.startswith("ERROR "):
                if current_failure:
                    result["failure_details"].append(current_failure)
                in_failure = True
                current_failure = {"line": stripped, "context": []}
            elif in_failure and current_failure is not None:
                if stripped.startswith("____") or stripped.startswith("==="):
                    in_failure = False
                    if current_failure:
                        result["failure_details"].append(current_failure)
                        current_failure = None
                elif stripped:
                    if len(current_failure["context"]) < 8:
                        current_failure["context"].append(stripped)
        if current_failure:
            result["failure_details"].append(current_failure)

    return result


def run_pytest_suite(suite: dict) -> dict:
    """执行单个测试套件 (pytest 或 python 独立脚本)."""
    started = time.time()
    abs_path = BACKEND_DIR / suite["path"]
    runner = suite.get("runner", "pytest")
    record = {
        "name": suite["name"],
        "path": str(suite["path"]),
        "description": suite["description"],
        "category": suite["category"],
        "runner": runner,
        "block_on_fail": suite["block_on_fail"],
        "started_at": _now_iso(),
        "elapsed_sec": 0.0,
        "returncode": None,
        "summary": {},
        "raw_output_tail": "",
    }

    if not abs_path.exists():
        record["returncode"] = -1
        record["error"] = f"测试文件不存在: {abs_path}"
        record["elapsed_sec"] = time.time() - started
        return record

    # 构造命令
    if runner == "pytest":
        cmd = [
            sys.executable, "-m", "pytest",
            str(suite["path"]),
            "-v", "--tb=short", "--color=no",
        ]
    elif runner == "python":
        cmd = [sys.executable, str(suite["path"])]
    else:
        record["returncode"] = -4
        record["error"] = f"未知 runner 类型: {runner}"
        record["elapsed_sec"] = time.time() - started
        return record

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    # 将项目根目录加入 PYTHONPATH, 使 'from backend.xxx' 导入生效
    project_root_str = str(PROJECT_ROOT)
    existing_path = env.get("PYTHONPATH", "")
    if project_root_str not in existing_path.split(os.pathsep):
        env["PYTHONPATH"] = project_root_str + (os.pathsep + existing_path if existing_path else "")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=120,
        )
        record["returncode"] = proc.returncode
        full_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if runner == "pytest":
            record["summary"] = _parse_pytest_output(full_output, proc.returncode)
        else:
            # 独立脚本: 退出码 0=通过, 非 0=失败
            record["summary"] = {
                "total": 1,
                "passed": 1 if proc.returncode == 0 else 0,
                "failed": 0 if proc.returncode == 0 else 1,
                "skipped": 0,
                "errors": 0,
                "duration_sec": 0.0,
                "failure_details": [] if proc.returncode == 0 else [
                    {"line": f"退出码 {proc.returncode}", "context": []}
                ],
            }
        # 仅保留尾部 50 行, 避免报告过大
        tail_lines = full_output.strip().splitlines()[-50:]
        record["raw_output_tail"] = "\n".join(tail_lines)
    except subprocess.TimeoutExpired as exc:
        record["returncode"] = -2
        record["error"] = f"测试超时 (120s): {exc}"
    except Exception as exc:
        record["returncode"] = -3
        record["error"] = f"执行异常: {type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()

    record["elapsed_sec"] = time.time() - started
    return record


# ============================================================
# 报告生成
# ============================================================
def build_text_report(suite_results, total_elapsed, summary, env_info):
    lines = []
    lines.append("=" * 78)
    lines.append("  Pre-Commit 自动化测试报告")
    lines.append("=" * 78)
    lines.append(f"生成时间:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"操作系统:    {env_info['os']} ({env_info['platform']})")
    lines.append(f"Python 版本: {env_info['python']}")
    lines.append(f"项目根目录:  {env_info['project_root']}")
    lines.append(f"总耗时:      {_format_duration(total_elapsed)}")
    lines.append("=" * 78)
    lines.append("")

    # 摘要
    lines.append("【1. 测试摘要】")
    lines.append(f"  - 测试套件数:   {summary['total_suites']}")
    lines.append(f"  - 通过:         {summary['passed_suites']}")
    lines.append(f"  - 失败:         {summary['failed_suites']}")
    lines.append(f"  - 用例总数:     {summary['total_cases']}")
    lines.append(f"  - 通过用例:     {summary['passed_cases']}")
    lines.append(f"  - 失败用例:     {summary['failed_cases']}")
    lines.append(f"  - 跳过用例:     {summary['skipped_cases']}")
    lines.append(f"  - 错误用例:     {summary['error_cases']}")
    lines.append(f"  - 阻断 commit:  {'是 (FAIL)' if summary['block_commit'] else '否 (PASS)'}")
    lines.append(f"  - 退出码:       {summary['exit_code']}")
    lines.append("")

    # 各套件详情
    lines.append("【2. 测试套件详情】")
    for idx, rec in enumerate(suite_results, 1):
        lines.append("")
        lines.append(f"  [{idx}] {rec['name']}")
        lines.append(f"      路径:       {rec['path']}")
        lines.append(f"      分类:       {rec['category']}")
        lines.append(f"      阻断失败:   {'是' if rec['block_on_fail'] else '否'}")
        lines.append(f"      启动时间:   {rec['started_at']}")
        lines.append(f"      耗时:       {_format_duration(rec['elapsed_sec'])}")
        if "error" in rec:
            lines.append(f"      执行错误:   {rec['error']}")
        if rec['summary']:
            s = rec['summary']
            lines.append(f"      返回码:     {rec['returncode']}")
            lines.append(f"      用例总数:   {s['total']}")
            lines.append(f"      通过:       {s['passed']}")
            lines.append(f"      失败:       {s['failed']}")
            lines.append(f"      跳过:       {s['skipped']}")
            lines.append(f"      错误:       {s['errors']}")
            if s['failure_details']:
                lines.append("      失败详情 (前 5 条):")
                for fd in s['failure_details'][:5]:
                    lines.append(f"        - {fd['line']}")
        else:
            lines.append(f"      状态:       无法解析 (returncode={rec['returncode']})")

    # 失败详情全文
    lines.append("")
    lines.append("【3. 失败用例原始输出 (尾部 30 行)】")
    for idx, rec in enumerate(suite_results, 1):
        if rec['summary'].get('failure_details') or rec.get('error'):
            lines.append("")
            lines.append(f"  --- {rec['name']} ---")
            lines.append(rec.get('raw_output_tail', ''))

    # 结论
    lines.append("")
    lines.append("=" * 78)
    lines.append("【4. 结论】")
    lines.append("=" * 78)
    if summary['block_commit']:
        lines.append(f"  存在 {summary['failed_cases']} 个失败用例.")
        lines.append("  阻断 commit, 请修复后重试.")
        lines.append("")
        lines.append("  修复建议:")
        lines.append("    1. 查看失败用例详情, 定位根因")
        lines.append("    2. 修改代码后重新执行: python scripts/pre_commit_tests.py")
        lines.append("    3. 通过后重新 git commit")
    else:
        lines.append("  全部测试通过, commit 已放行.")
        lines.append("")
        lines.append("  验证范围:")
        lines.append("    1. HRC 公式修复 (HB=200 → 符合 ASTM E140)")
        lines.append("    2. Tolerance 配合计算 + 日志格式 (4 条 INFO, 含 ts= + rule=)")
        lines.append("    3. H7/k6/H7/m6/H7/n6 过渡配合端到端")
    lines.append("=" * 78)
    return "\n".join(lines)


def build_markdown_report(suite_results, total_elapsed, summary, env_info):
    md = []
    md.append("# Pre-Commit 自动化测试报告")
    md.append("")
    md.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"> 操作系统: {env_info['os']} ({env_info['platform']})")
    md.append(f"> Python: {env_info['python']}")
    md.append(f"> 总耗时: {_format_duration(total_elapsed)}")
    md.append("")

    # 状态徽章
    if summary['block_commit']:
        md.append("## 状态: ❌ 失败 - 阻断 commit")
    else:
        md.append("## 状态: ✅ 通过 - 允许 commit")
    md.append("")

    # 摘要表
    md.append("## 测试摘要")
    md.append("")
    md.append("| 指标 | 数值 |")
    md.append("|------|------|")
    md.append(f"| 测试套件总数 | {summary['total_suites']} |")
    md.append(f"| 通过套件 | {summary['passed_suites']} |")
    md.append(f"| 失败套件 | {summary['failed_suites']} |")
    md.append(f"| 用例总数 | {summary['total_cases']} |")
    md.append(f"| 通过用例 | {summary['passed_cases']} |")
    md.append(f"| 失败用例 | {summary['failed_cases']} |")
    md.append(f"| 跳过用例 | {summary['skipped_cases']} |")
    md.append(f"| 错误用例 | {summary['error_cases']} |")
    md.append(f"| 退出码 | {summary['exit_code']} |")
    md.append("")

    # 套件详情
    md.append("## 测试套件详情")
    md.append("")
    md.append("| # | 套件 | 分类 | 用例 | 通过 | 失败 | 跳过 | 错误 | 耗时 | 状态 |")
    md.append("|---|------|------|------|------|------|------|------|------|------|")
    for idx, rec in enumerate(suite_results, 1):
        s = rec.get('summary', {})
        status = "✅" if s.get('failed', 0) == 0 and not rec.get('error') else "❌"
        md.append(
            f"| {idx} | {rec['name']} | {rec['category']} | "
            f"{s.get('total', 0)} | {s.get('passed', 0)} | "
            f"{s.get('failed', 0)} | {s.get('skipped', 0)} | "
            f"{s.get('errors', 0)} | "
            f"{_format_duration(rec['elapsed_sec'])} | {status} |"
        )
    md.append("")

    # 失败详情
    has_failures = any(
        rec.get('summary', {}).get('failure_details') or rec.get('error')
        for rec in suite_results
    )
    if has_failures:
        md.append("## 失败详情")
        md.append("")
        for rec in suite_results:
            if rec.get('error'):
                md.append(f"### {rec['name']} - 执行错误")
                md.append("```")
                md.append(rec['error'])
                md.append("```")
                md.append("")

            for fd in rec.get('summary', {}).get('failure_details', []):
                md.append(f"### {rec['name']} - 失败用例")
                md.append("```")
                md.append(fd.get('line', ''))
                for ctx in fd.get('context', [])[:10]:
                    md.append(ctx)
                md.append("```")
                md.append("")

    return "\n".join(md)


# ============================================================
# 主流程
# ============================================================
def main() -> int:
    t_start = time.time()

    env_info = {
        "os": platform.system(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "project_root": str(PROJECT_ROOT),
        "backend_dir": str(BACKEND_DIR),
    }

    print("=" * 78)
    print("  Pre-Commit 自动化测试")
    print("=" * 78)
    print(f"  时间:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python: {env_info['python']}")
    print(f"  后端目录: {env_info['backend_dir']}")
    print(f"  测试套件: {len(TEST_SUITES)} 个")
    print("=" * 78)
    print()

    suite_results = []
    for idx, suite in enumerate(TEST_SUITES, 1):
        print(f"  [{idx}/{len(TEST_SUITES)}] {suite['name']}")
        print(f"    路径: {suite['path']}")
        rec = run_pytest_suite(suite)
        suite_results.append(rec)

        if "error" in rec:
            print(f"    ❌ 执行错误: {rec['error']}")
        else:
            s = rec['summary']
            verdict = "✅" if s.get('failed', 0) == 0 and s.get('errors', 0) == 0 else "❌"
            print(
                f"    {verdict} {s.get('passed', 0)} passed, "
                f"{s.get('failed', 0)} failed, "
                f"{s.get('skipped', 0)} skipped, "
                f"{s.get('errors', 0)} errors "
                f"({_format_duration(rec['elapsed_sec'])})"
            )
        print()

    total_elapsed = time.time() - t_start

    # 汇总
    total_cases = sum(r['summary'].get('total', 0) for r in suite_results)
    passed_cases = sum(r['summary'].get('passed', 0) for r in suite_results)
    failed_cases = sum(r['summary'].get('failed', 0) for r in suite_results)
    skipped_cases = sum(r['summary'].get('skipped', 0) for r in suite_results)
    error_cases = sum(r['summary'].get('errors', 0) for r in suite_results)

    passed_suites = sum(
        1 for r in suite_results
        if r['summary'].get('failed', 0) == 0
        and r['summary'].get('errors', 0) == 0  # noqa: W503
        and not r.get('error')  # noqa: W503
    )
    failed_suites = len(suite_results) - passed_suites
    block_commit = failed_suites > 0

    summary = {
        "total_suites": len(suite_results),
        "passed_suites": passed_suites,
        "failed_suites": failed_suites,
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "skipped_cases": skipped_cases,
        "error_cases": error_cases,
        "block_commit": block_commit,
        "exit_code": 1 if block_commit else 0,
    }

    # 打印摘要
    print("=" * 78)
    print(f"  摘要: {passed_suites}/{len(suite_results)} 套件通过, "
          f"{passed_cases}/{total_cases} 用例通过")
    print(f"  耗时: {_format_duration(total_elapsed)}")
    print(f"  决策: {'阻断 commit (❌ FAIL)' if block_commit else '放行 commit (✅ PASS)'}")
    print("=" * 78)
    print()

    # 生成报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_path = REPORT_DIR / f"pre_commit_{timestamp}.txt"
    md_path = REPORT_DIR / f"pre_commit_{timestamp}.md"
    json_path = REPORT_DIR / f"pre_commit_{timestamp}.json"
    latest_txt = REPORT_DIR / "pre_commit_latest.txt"
    latest_md = REPORT_DIR / "pre_commit_latest.md"
    latest_json = REPORT_DIR / "pre_commit_latest.json"

    # 文本报告
    txt_content = build_text_report(suite_results, total_elapsed, summary, env_info)
    txt_path.write_text(txt_content, encoding="utf-8")
    latest_txt.write_text(txt_content, encoding="utf-8")

    # Markdown 报告
    md_content = build_markdown_report(suite_results, total_elapsed, summary, env_info)
    md_path.write_text(md_content, encoding="utf-8")
    latest_md.write_text(md_content, encoding="utf-8")

    # JSON 报告
    json_data = {
        "generated_at": _now_iso(),
        "env": env_info,
        "summary": summary,
        "total_elapsed_sec": total_elapsed,
        "suites": suite_results,
    }
    json_path.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    latest_json.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print("  报告已生成:")
    print(f"    文本:   {txt_path}")
    print(f"    Markdown: {md_path}")
    print(f"    JSON:  {json_path}")
    print(f"    最新:  {latest_txt}")
    print()

    return summary["exit_code"]


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n用户中断 (Ctrl+C)", file=sys.stderr)
        sys.exit(3)
