"""
Pre-Commit Hook 安装/卸载脚本
=============================

功能:
    - 安装: 将 git_pre_commit_hook.py 复制到 .git/hooks/pre-commit
    - 卸载: 删除 .git/hooks/pre-commit
    - 状态: 检查当前 hook 安装状态

使用:
    # 安装
    python backend/scripts/install_pre_commit_hook.py install

    # 卸载
    python backend/scripts/install_pre_commit_hook.py uninstall

    # 查看状态
    python backend/scripts/install_pre_commit_hook.py status
"""
import os
import shutil
import stat
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

HOOK_SOURCE = SCRIPT_DIR / "git_pre_commit_hook.py"
GIT_DIR = PROJECT_ROOT / ".git"
HOOKS_DIR = GIT_DIR / "hooks"
HOOK_TARGET = HOOKS_DIR / "pre-commit"


def print_color(text: str, color: str) -> None:
    """跨平台彩色输出."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m",
    }
    if os.name == "nt":
        os.system("color")
    print(f"{colors.get(color, '')}{text}{colors['reset']}")


def check_git_repo() -> bool:
    if not GIT_DIR.exists():
        print_color(f"❌ 错误: {PROJECT_ROOT} 不是 git 仓库 (缺少 .git 目录)", "red")
        return False
    return True


def cmd_install() -> int:
    """安装 pre-commit hook."""
    print_color("=" * 60, "blue")
    print_color("  安装 Git Pre-Commit Hook", "blue")
    print_color("=" * 60, "blue")
    print()

    if not check_git_repo():
        return 1

    if not HOOK_SOURCE.exists():
        print_color(f"❌ 源文件不存在: {HOOK_SOURCE}", "red")
        return 1

    # 创建 hooks 目录
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)

    # 检查是否已存在
    if HOOK_TARGET.exists():
        print_color(f"⚠️  目标文件已存在: {HOOK_TARGET}", "yellow")
        response = input("是否覆盖? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print_color("已取消安装", "yellow")
            return 0
        HOOK_TARGET.unlink()

    # 复制文件
    shutil.copy2(HOOK_SOURCE, HOOK_TARGET)

    # 设置可执行权限 (Windows 下无需, Unix/Mac 需要)
    if os.name != "nt":
        current_mode = HOOK_TARGET.stat().st_mode
        HOOK_TARGET.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print_color(f"✅ 已安装: {HOOK_TARGET}", "green")
    print()
    print("  安装信息:")
    print(f"    源文件: {HOOK_SOURCE}")
    print(f"    目标:   {HOOK_TARGET}")
    print(f"    大小:   {HOOK_TARGET.stat().st_size} bytes")
    print()
    print("  测试方法:")
    print("    1. 尝试执行 git commit, 应自动触发测试")
    print("    2. 或手动测试: python backend/scripts/pre_commit_tests.py")
    print()
    print("  卸载方法:")
    print("    python backend/scripts/install_pre_commit_hook.py uninstall")
    return 0


def cmd_uninstall() -> int:
    """卸载 pre-commit hook."""
    print_color("=" * 60, "blue")
    print_color("  卸载 Git Pre-Commit Hook", "blue")
    print_color("=" * 60, "blue")
    print()

    if not HOOK_TARGET.exists():
        print_color(f"⚠️  Hook 未安装 (目标不存在): {HOOK_TARGET}", "yellow")
        return 0

    HOOK_TARGET.unlink()
    print_color(f"✅ 已卸载: {HOOK_TARGET}", "green")
    return 0


def cmd_status() -> int:
    """查看 hook 状态."""
    print_color("=" * 60, "blue")
    print_color("  Pre-Commit Hook 状态", "blue")
    print_color("=" * 60, "blue")
    print()

    print(f"  Git 仓库:  {PROJECT_ROOT}")
    print(f"  .git 目录: {'存在' if GIT_DIR.exists() else '不存在'}")
    print()

    if not GIT_DIR.exists():
        return 1

    print(f"  Hook 源文件:  {HOOK_SOURCE}")
    print(f"  Hook 目标:    {HOOK_TARGET}")
    print()

    if HOOK_TARGET.exists():
        print_color("  状态: ✅ 已安装", "green")
        size = HOOK_TARGET.stat().st_size
        print(f"  大小: {size} bytes")
        if os.name != "nt":
            mode = oct(HOOK_TARGET.stat().st_mode)[-3:]
            print(f"  权限: {mode}")
        # 验证文件内容是否匹配
        if HOOK_SOURCE.exists():
            src_hash = _file_hash(HOOK_SOURCE)
            tgt_hash = _file_hash(HOOK_TARGET)
            if src_hash == tgt_hash:
                print_color("  源/目标一致: ✅", "green")
            else:
                print_color("  源/目标不一致: ⚠️  建议重新安装", "yellow")
    else:
        print_color("  状态: ❌ 未安装", "red")
        print()
        print("  安装方法: python backend/scripts/install_pre_commit_hook.py install")
    return 0


def _file_hash(path: Path) -> str:
    """计算文件 SHA256 (前 16 字符)."""
    import hashlib
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python install_pre_commit_hook.py [install|uninstall|status]")
        print()
        print("命令:")
        print("  install   - 安装 pre-commit hook")
        print("  uninstall - 卸载 pre-commit hook")
        print("  status    - 查看 hook 状态")
        return 0

    cmd = sys.argv[1].lower()
    if cmd in ("install", "i"):
        return cmd_install()
    elif cmd in ("uninstall", "u", "remove"):
        return cmd_uninstall()
    elif cmd in ("status", "s"):
        return cmd_status()
    else:
        print(f"未知命令: {cmd}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
