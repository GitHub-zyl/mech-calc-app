# Pre-Commit 自动化测试系统

本目录包含项目的 pre-commit 自动化测试基础设施，确保每次 `git commit` 前自动运行关键测试。

---

## 文件清单

| 文件 | 作用 |
|------|------|
| `pre_commit_tests.py` | 核心: 执行所有测试套件并生成报告 |
| `git_pre_commit_hook.py` | Git Hook 源文件: 被复制到 `.git/hooks/pre-commit` |
| `install_pre_commit_hook.py` | 安装/卸载工具 |
| `pre_commit_tests.bat` | Windows 批处理包装 (双击或 cmd 运行) |
| `pre_commit_tests.sh` | Linux/Mac Bash 包装 |

---

## 快速开始

### 1. 安装 Git Hook

```bash
# 进入后端目录
cd backend

# 安装
python scripts/install_pre_commit_hook.py install

# 查看状态
python scripts/install_pre_commit_hook.py status

# 卸载
python scripts/install_pre_commit_hook.py uninstall
```

安装后，每次执行 `git commit` 都会自动运行测试。

### 2. 手动运行测试

```bash
# Python (跨平台)
python scripts/pre_commit_tests.py

# Windows 批处理
scripts\pre_commit_tests.bat

# Linux/Mac Bash
./scripts/pre_commit_tests.sh
```

### 3. 跳过 Hook（紧急情况）

```bash
git commit --no-verify -m "emergency fix"
```

---

## 测试套件配置

`pre_commit_tests.py` 中 `TEST_SUITES` 列表定义要运行的测试：

```python
TEST_SUITES = [
    {
        "name": "HRC 公式 (HB=200 修复点)",
        "path": "tests/integration/test_hrc_hb200_standard.py",
        "description": "...",
        "block_on_fail": True,
        "runner": "pytest",  # 或 "python" 独立脚本
        "category": "integration",
    },
    # ...
]
```

| 字段 | 含义 |
|------|------|
| `name` | 套件显示名 |
| `path` | 相对 `backend/` 的测试文件路径 |
| `runner` | `pytest` (pytest 测试) 或 `python` (独立脚本) |
| `block_on_fail` | 失败时是否阻断 commit |
| `category` | 分类标签 (`unit` / `integration` / `smoke`) |

---

## 报告输出

每次执行生成 3 种格式报告 + latest 软链接：

| 格式 | 路径 |
|------|------|
| 文本 | `docs/coverage/pre_commit/pre_commit_YYYYMMDD_HHMMSS.txt` |
| Markdown | `docs/coverage/pre_commit/pre_commit_YYYYMMDD_HHMMSS.md` |
| JSON | `docs/coverage/pre_commit/pre_commit_YYYYMMDD_HHMMSS.json` |
| 最新 | `docs/coverage/pre_commit/pre_commit_latest.{txt,md,json}` |

报告内容：
- 测试套件总数 / 通过 / 失败
- 用例总数 / 通过 / 失败 / 跳过 / 错误
- 退出码与阻断决策
- 每个套件的详细耗时与状态
- 失败用例的原始输出尾部

---

## 当前覆盖范围

| 套件 | 路径 | 用途 |
|------|------|------|
| HRC 公式 (HB=200) | `tests/integration/test_hrc_hb200_standard.py` | 验证 HRC 公式修复，防止回退到 70 错误 |
| Tolerance 配合 + 日志 | `tests/unit/test_calculations_tolerance.py` | 验证 fit_calculation + 优化后日志格式 |
| H7 过渡配合 | `tests/test_h7_transition_fits.py` | 端到端测试 H7/k6、H7/m6、H7/n6 |

合计 111 个测试用例。

---

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 全部通过, 允许 commit |
| 1 | 存在测试失败, 阻断 commit |
| 2 | 执行环境异常 (如 pytest 未安装) |
| 3 | 用户中断 (Ctrl+C) |

---

## 故障排查

### Q1: Hook 不触发

确认 `.git/hooks/pre-commit` 文件存在且有可执行权限：

```bash
ls -la .git/hooks/pre-commit    # Unix/Mac
dir .git\hooks\pre-commit       # Windows
```

重新安装：`python scripts/install_pre_commit_hook.py install`

### Q2: 中文乱码

Windows PowerShell 默认编码非 UTF-8，可能出现中文乱码。脚本已设置 `PYTHONIOENCODING=utf-8`，但终端仍可能显示异常——**实际生成的报告文件是 UTF-8 编码，无乱码**。

### Q3: 测试解析失败

若 pytest 输出格式变更导致 `_parse_pytest_output` 解析失败，错误会显示在报告中。检查 `pre_commit_tests.py` 中的正则表达式。

---

## 最佳实践

1. **定期清理旧报告**: 报告按时间戳累积，建议每月清理：
   ```bash
   find docs/coverage/pre_commit -name "pre_commit_2*" -mtime +30 -delete
   ```

2. **新增加速测试**: 核心逻辑变更时优先扩展 `TEST_SUITES`，确保回归保护。

3. **查看 latest 报告**: CI/IDE 集成时直接读取 `pre_commit_latest.md`。

4. **保留多种格式**: 文本给 CI 日志，Markdown 给文档/邮件，JSON 给自动化处理。
