#!/usr/bin/env python
"""
Git Pre-Commit Hook
===================

文件路径: .git/hooks/pre-commit
触发时机: 每次 `git commit` 前自动执行
作用: 调用 backend/scripts/pre_commit_tests.py 执行测试套件
      若任何测试失败, 阻断 commit (退出码非 0)
"""
import os
import subprocess
import sys
from pathlib import Path

# 计算项目根目录: .git/hooks/pre-commit → .git/hooks → .git → 项目根
HOOK_PATH = Path(__file__).resolve()
GIT_HOOKS_DIR = HOOK_PATH.parent
GIT_DIR = GIT_HOOKS_DIR.parent
PROJECT_ROOT = GIT_DIR

# 后端目录
BACKEND_DIR = PROJECT_ROOT / "backend"
TEST_SCRIPT = BACKEND_DIR / "scripts" / "pre_commit_tests.py"


def main() -> int:
    # 检查是否在项目根目录
    if not TEST_SCRIPT.exists():
        print(f"❌ 错误: 找不到测试脚本 {TEST_SCRIPT}", file=sys.stderr)
        print(f"   请确认项目结构, 或重新运行 install_pre_commit_hook.py",
              file=sys.stderr)
        return 1

    # Windows 下显示彩色提示
    if os.name == "nt":
        os.system("color")

    print("=" * 60)
    print("  Git Pre-Commit Hook: 自动化测试")
    print("=" * 60)
    print(f"  触发原因: 即将执行 git commit")
    print(f"  执行脚本: {TEST_SCRIPT.relative_to(PROJECT_ROOT)}")
    print("=" * 60)
    print()

    # 调用测试脚本
    try:
        result = subprocess.run(
            [sys.executable, str(TEST_SCRIPT)],
            cwd=str(PROJECT_ROOT),
            check=False,
        )
    except KeyboardInterrupt:
        print("\n用户中断", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"❌ 执行异常: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    # 根据测试结果决定是否阻断 commit
    if result.returncode == 0:
        print()
        print("=" * 60)
        print("  ✅ 所有测试通过, 允许 commit")
        print("=" * 60)
        return 0
    else:
        print()
        print("=" * 60)
        print(f"  ❌ 测试失败 (退出码 {result.returncode}), 阻断 commit")
        print("  修复失败的测试后, 重新执行 git commit")
        print("=" * 60)
        print()
        print("  跳过 pre-commit hook (紧急情况):")
        print("    git commit --no-verify")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
