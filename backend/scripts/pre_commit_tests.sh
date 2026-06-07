#!/usr/bin/env bash
# Pre-Commit 自动化测试 (Bash 包装)
# 用法: ./pre_commit_tests.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/pre_commit_tests.py"

echo "============================================================"
echo "  Pre-Commit 自动化测试 (Bash 包装)"
echo "============================================================"
echo "  脚本路径: $PYTHON_SCRIPT"
echo "  后端目录: $BACKEND_DIR"
echo "============================================================"

cd "$BACKEND_DIR"
python3 "$PYTHON_SCRIPT"

EXITCODE=$?

echo
if [ $EXITCODE -eq 0 ]; then
    echo "============================================================"
    echo "  ✅ 所有测试通过"
    echo "============================================================"
else
    echo "============================================================"
    echo "  ❌ 测试失败, 退出码: $EXITCODE"
    echo "============================================================"
fi

exit $EXITCODE
