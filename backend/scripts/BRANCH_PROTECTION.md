# Required Status Check 合并保护配置指南

本目录脚本用于将 `pre-commit-tests` job 配置为 GitHub develop 分支的 **Required Status Check**，阻止未通过测试的代码合并到 develop 分支。

## 核心概念

### Required Check 名称格式

GitHub Required Status Check 的完整名称格式为：

```
<workflow_name> / <job_id>
```

当前工作流:

| 项目 | 值 |
|------|------|
| Workflow 名称 | `Tests` |
| Job ID | `pre-commit-tests` |
| **完整 Required Check 名称** | **`Tests / pre-commit-tests`** |

> 重要: 不要随意修改 [tests.yml](../../workflows/tests.yml#L225-L226) 中 `name: pre-commit-tests`, 一旦修改, 之前配置的 required check 名称会失效, 需重新配置.

## 文件清单

| 文件 | 用途 |
|------|------|
| `setup_branch_protection.ps1` | **Windows** (PowerShell 5.1+) 一键配置脚本 |
| `setup_branch_protection.sh` | **Linux / macOS** / Git Bash 一键配置脚本 |
| `README.md` | 本说明文档 |

## 使用方法

### 方式 1: GitHub 网页手动配置 (推荐首次使用)

1. 打开 GitHub 仓库页面 → `Settings` → `Branches` → `Add branch protection rule`
2. **Branch name pattern**: `develop`
3. 勾选以下选项:
   - ☑ `Require a pull request before merging`
     - ☑ `Require approvals`: 1
   - ☑ `Dismiss stale pull request approvals when new commits are pushed`
   - ☑ `Require conversation resolution before merging`
4. 勾选 `Require status checks to pass before merging`
   - ☑ `Require branches to be up to date before merging`
   - 在搜索框输入 `Tests / pre-commit-tests` 并勾选
5. 勾选 `Require linear history` (可选, 推荐)
6. **不要**勾选:
   - ❌ `Allow force pushes` (生产分支禁止)
   - ❌ `Allow deletions` (生产分支禁止)
   - ❌ `Enforce_admins` (允许 maintainer 紧急 hotfix, 但需谨慎)
7. 点击 `Create` / `Save changes`

### 方式 2: 自动化脚本配置

#### Windows (PowerShell)

```powershell
cd 'c:\Users\Administrator\机械计算小程序\backend\scripts'
.\setup_branch_protection.ps1
```

脚本流程:

1. 检查 `gh` CLI 是否安装
2. 检查 GitHub 认证状态
3. 自动检测仓库 owner/repo
4. 检查目标分支是否存在
5. 检查 admin 权限
6. 显示配置预览, 等待用户确认
7. 调用 GitHub REST API 应用规则
8. 输出当前规则详情

#### Linux / macOS / Git Bash

```bash
cd /path/to/机械计算小程序/backend/scripts
chmod +x setup_branch_protection.sh
./setup_branch_protection.sh
```

## 配置项说明

| 配置项 | 值 | 说明 |
|--------|----|-----|
| `required_status_checks.strict` | `true` | 要求分支 up-to-date 才能合并 |
| `required_status_checks.contexts` | `["Tests / pre-commit-tests"]` | 必须通过的 check 列表 |
| `required_pull_request_reviews.dismiss_stale_reviews` | `true` | 新 commit 提交后, 旧 review 自动失效 |
| `required_pull_request_reviews.required_approving_review_count` | `1` | 至少 1 个 reviewer approval |
| `required_linear_history` | `true` | 强制线性历史, 禁止 merge commit |
| `allow_force_pushes` | `false` | 禁止 force push |
| `allow_deletions` | `false` | 禁止删除保护分支 |
| `enforce_admins` | `false` | 允许 maintainer 绕过规则 (紧急 hotfix) |

## 验证配置

### 命令行验证

```bash
gh api repos/<OWNER>/<REPO>/branches/develop/protection
```

预期输出 (节选):

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Tests / pre-commit-tests"]
  },
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "required_approving_review_count": 1
  },
  ...
}
```

### UI 验证

`Settings` → `Branches` → `develop` → 看到 "Required status checks" 列表中有 `Tests / pre-commit-tests` ✓

### 端到端验证

1. 新建一个故意失败的测试
2. 提交 PR 到 develop
3. 观察 GitHub Actions 状态:
   - `Tests / pre-commit-tests` 显示 ❌
   - PR 顶部显示 "Merging is blocked"
4. 修复测试, 重新 push
5. 状态变绿后, "Merge pull request" 按钮变为可点击

## 故障排查

### 1. Required check 名称不匹配

**症状**: PR 提交后, UI 提示 "Waiting for status to be reported", 但 Actions 早已完成

**原因**: branch protection 中配置的 check 名称与 workflow 中 job 名称不一致

**修复**:
1. 访问 PR 页面的 `Checks` tab
2. 找到 PR 实际生成的 check 名称 (例如 `Tests / pre-commit-tests`)
3. 在 branch protection 中修改为该名称
4. 重新推送 PR 验证

### 2. 权限不足

**症状**: 脚本提示 "Current user lacks admin permission"

**修复**:
1. 访问 `Settings` → `Collaborators and teams`
2. 确认当前用户在 `Admin` 或 `Maintain` 角色
3. 重新运行脚本

### 3. 分支不存在

**症状**: 脚本提示 "Branch develop may not exist"

**修复**:
1. 确认远程有 develop 分支: `git branch -r | grep develop`
2. 如不存在, 先 push: `git push origin develop`
3. 重新运行脚本

### 4. gh CLI 未安装

**症状**: 脚本提示 "gh CLI not found"

**修复**:
```powershell
winget install --id GitHub.cli
```

```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
sudo apt install gh
```

安装后执行 `gh auth login` 完成认证。

## 紧急绕过

如果 CI 故障导致所有 PR 被卡住, 可临时绕过:

### 方案 1: 管理员绕过 (推荐)

在 `Settings` → `Branches` → `develop` 中临时开启 `Enforce_admins`, 此时 admin 可绕过规则推送。

### 方案 2: PR 临时禁用 required check

在 PR 页面 → `Edit` 底部, 部分 GitHub 版本支持 "Require status checks to pass" 临时关闭。

### 方案 3: 紧急合并

```bash
git checkout develop
git merge feature/xxx --no-verify
git push origin develop
```

⚠️ **警告**: 此方式会绕过所有保护, 须团队 lead 授权。

## 进一步加固

- **CODEOWNERS**: 在 `.github/CODEOWNERS` 中指定关键模块的 owner, 触发自动 reviewer 分配
- **Signed commits**: 在 branch protection 中启用 `Require signed commits`
- **Dependabot**: 启用自动依赖更新
- **PR template**: 在 `.github/PULL_REQUEST_TEMPLATE.md` 中规范化 PR 描述

## 参考

- [GitHub Docs: Branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Docs: Required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- [GitHub REST API: Update branch protection](https://docs.github.com/en/rest/branches/branch-protection?apiVersion=2022-11-28#update-branch-protection)
- [gh CLI Manual](https://cli.github.com/manual/)
