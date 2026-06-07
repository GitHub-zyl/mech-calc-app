@echo off
:: Pre-Commit 自动化测试 (Windows 批处理包装)
:: 用法: pre_commit_tests.bat

setlocal

set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%SCRIPT_DIR%pre_commit_tests.py

echo ============================================================
echo   Pre-Commit 自动化测试 (Windows 包装)
echo ============================================================
echo   脚本路径: %PYTHON_SCRIPT%
echo   后端目录: %BACKEND_DIR%
echo ============================================================
echo.

cd /d "%BACKEND_DIR%"
python "%PYTHON_SCRIPT%"

set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE% EQU 0 (
    echo ============================================================
    echo   ✅ 所有测试通过
    echo ============================================================
) else (
    echo ============================================================
    echo   ❌ 测试失败, 退出码: %EXITCODE%
    echo ============================================================
)

endlocal & exit /b %EXITCODE%
