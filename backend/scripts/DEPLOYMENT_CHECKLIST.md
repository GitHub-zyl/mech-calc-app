# 主项目部署操作清单

## 概述

本清单涵盖将机械计算小程序项目从本地开发环境部署到 GitHub 远程仓库的完整流程，包括：
1. Git remote 配置
2. 分支保护规则应用
3. CI/CD 流水线验证
4. gh CLI 备选方案
5. 首次部署自动配置集成

---

## 一、Git Remote 配置

### 1.1 创建 GitHub 仓库

```powershell
# 方式 A: 使用 gh CLI (推荐)
gh repo create <REPO_NAME> --public --description "机械计算小程序"

# 方式 B: 使用 gh CLI 创建到指定组织
gh repo create <ORG>/<REPO_NAME> --public --description "机械计算小程序"

# 方式 C: 在 GitHub 网页创建
# https://github.com/new
```

### 1.2 添加 Remote 并推送

```powershell
cd "c:\Users\Administrator\机械计算小程序"

# 添加 remote
git remote add origin https://github.com/<OWNER>/<REPO_NAME>.git

# 验证 remote
git remote -v

# 推送主分支
git push -u origin master

# 创建并推送 develop 分支
git checkout -b develop
git push -u origin develop

# 切回 master
git checkout master
```

### 1.3 设置默认分支

```powershell
# 如果希望 develop 为默认分支
gh repo edit --default-branch develop

# 验证
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

### 1.4 推送 CI/CD 配置

```powershell
# 确保 .github/workflows/ 目录已提交
git add .github/workflows/tests.yml
git add .github/workflows/coverage.yml
git add .github/workflows/lint.yml
git commit -m "ci: add GitHub Actions workflows"
git push origin master

# 同步到 develop
git checkout develop
git merge master
git push origin develop
```

---

## 二、分支保护规则应用

### 2.1 方式 A: PowerShell 脚本 (推荐)

```powershell
cd "c:\Users\Administrator\机械计算小程序\backend\scripts"

# 交互模式 (逐步确认)
.\setup_branch_protection.ps1 -Branch develop

# 非交互模式 (CI/CD 友好)
.\setup_branch_protection.ps1 -Branch develop -AutoConfirm

# 指定仓库 (不在 git 仓库内时)
.\setup_branch_protection.ps1 -Owner "GitHub-zyl" -Repo "机械计算小程序" -Branch develop -AutoConfirm
```

### 2.2 方式 B: GitHub 网页手动配置

1. 打开 `https://github.com/<OWNER>/<REPO_NAME>/settings/branches`
2. 点击 `Add branch protection rule`
3. **Branch name pattern**: `develop`
4. 勾选:
   - ☑ Require a pull request before merging
     - ☑ Require approvals: 1
     - ☑ Dismiss stale pull request approvals when new commits are pushed
   - ☑ Require conversation resolution before merging
   - ☑ Require status checks to pass before merging
     - ☑ Require branches to be up to date before merging
     - 搜索并勾选: `Tests / pre-commit-tests`
   - ☑ Require linear history
5. **不要**勾选:
   - ❌ Allow force pushes
   - ❌ Allow deletions
6. 点击 `Create`

### 2.3 方式 C: GitHub API 直接调用

```powershell
# 设置变量
$OWNER = "<OWNER>"
$REPO = "<REPO_NAME>"
$BRANCH = "develop"

# 创建保护规则 JSON
$protection = @'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Tests / pre-commit-tests"]
  },
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "enforce_admins": false,
  "required_signatures": false,
  "enabled": true
}
'@

# 写入临时文件
$tmpFile = [System.IO.Path]::GetTempFileName()
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tmpFile, $protection, $utf8NoBom)

# 调用 API
gh api --method PUT "repos/$OWNER/$REPO/branches/$BRANCH/protection" --input $tmpFile

# 清理
Remove-Item $tmpFile -Force
```

### 2.4 验证保护规则

```powershell
# 查看保护规则
gh api "repos/<OWNER>/<REPO_NAME>/branches/develop/protection"

# 仅查看 required checks
gh api "repos/<OWNER>/<REPO_NAME>/branches/develop/protection" --jq '.required_status_checks'
```

---

## 三、gh CLI 备选方案

### 3.1 场景: gh CLI 未安装

| 备选方案 | 操作步骤 | 优缺点 |
|----------|----------|--------|
| **GitHub 网页** | Settings → Branches → Add rule | 简单直观，但无法自动化 |
| **GitHub API + curl** | `curl -X PUT -H "Authorization: token $TOKEN" ...` | 可脚本化，但需手动管理 token |
| **GitHub API + Python** | 使用 `requests` 库调用 API | 可集成到部署脚本 |
| **Terraform** | `github_branch_protection` 资源 | 基础设施即代码，适合团队 |

#### Python 备选脚本 (无需 gh CLI)

```python
"""apply_branch_protection.py - 无需 gh CLI 的分支保护配置脚本"""
import os
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("[ERROR] 需要 requests 库: pip install requests")
    sys.exit(2)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OWNER = os.getenv("GITHUB_OWNER", "")
REPO = os.getenv("GITHUB_REPO", "")
BRANCH = os.getenv("PROTECTION_BRANCH", "develop")

if not GITHUB_TOKEN:
    print("[ERROR] 请设置 GITHUB_TOKEN 环境变量")
    print("  生成方式: https://github.com/settings/tokens")
    print("  所需权限: repo (full control)")
    sys.exit(3)

if not OWNER or not REPO:
    print("[ERROR] 请设置 GITHUB_OWNER 和 GITHUB_REPO 环境变量")
    sys.exit(4)

API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/branches/{BRANCH}/protection"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
}

PAYLOAD = {
    "required_status_checks": {
        "strict": True,
        "contexts": ["Tests / pre-commit-tests"],
    },
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": False,
        "required_approving_review_count": 1,
        "require_last_push_approval": False,
    },
    "restrictions": None,
    "required_linear_history": True,
    "allow_force_pushes": False,
    "allow_deletions": False,
    "block_creations": False,
    "required_conversation_resolution": True,
    "enforce_admins": False,
    "required_signatures": False,
    "enabled": True,
}

def main():
    print(f"配置分支保护: {OWNER}/{REPO} -> {BRANCH}")
    print(f"Required Check: Tests / pre-commit-tests")
    print()

    resp = requests.put(API_URL, headers=HEADERS, json=PAYLOAD)

    if resp.status_code == 200:
        data = resp.json()
        print("[OK] 分支保护规则已应用")
        print(f"  Strict: {data['required_status_checks']['strict']}")
        print(f"  Contexts: {data['required_status_checks']['contexts']}")
    elif resp.status_code == 401:
        print("[ERROR] 认证失败: GITHUB_TOKEN 无效或已过期")
        sys.exit(5)
    elif resp.status_code == 403:
        print("[ERROR] 权限不足: token 需要 repo 权限")
        sys.exit(6)
    elif resp.status_code == 404:
        print("[ERROR] 仓库或分支不存在")
        sys.exit(7)
    else:
        print(f"[ERROR] API 返回 {resp.status_code}: {resp.text}")
        sys.exit(8)

if __name__ == "__main__":
    main()
```

**使用方式:**

```powershell
# 安装依赖
pip install requests

# 设置环境变量
$env:GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
$env:GITHUB_OWNER = "GitHub-zyl"
$env:GITHUB_REPO = "机械计算小程序"

# 执行
python backend/scripts/apply_branch_protection.py
```

### 3.2 场景: gh CLI 认证失败

| 原因 | 解决方案 |
|------|----------|
| 未执行 `gh auth login` | 运行 `gh auth login` 按提示操作 |
| Token 过期 | `gh auth login` 重新认证 |
| 权限不足 (缺少 repo/workflow) | `gh auth login -s repo,workflow` |
| 企业 SSO | `gh auth login --hostname github.example.com` |
| 2FA 要求 | 使用 personal access token: `gh auth login --with-token` |

**自动化认证 (CI/CD 环境):**

```yaml
# GitHub Actions 中使用内置 GITHUB_TOKEN
- name: Apply branch protection
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    gh api --method PUT repos/${{ github.repository }}/branches/develop/protection \
      --input protection.json
```

### 3.3 场景: 无任何 CLI 工具

**纯 GitHub 网页操作:**

1. 打开 `https://github.com/<OWNER>/<REPO>/settings/branches`
2. 如无 admin 权限，请仓库 admin 操作
3. 按上面 "方式 B" 步骤配置

---

## 四、CI/CD 首次部署自动配置

### 4.1 方案: 在 CI 工作流中自动应用分支保护

在 `.github/workflows/tests.yml` 中添加 `setup-protection` job:

```yaml
  # ============== 首次部署: 自动配置分支保护 ==============
  setup-protection:
    name: 首次部署 - 配置分支保护
    runs-on: ubuntu-latest
    # 仅在 develop 分支首次推送时运行
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    # 仅运行一次 (检查保护规则是否已存在)
    outputs:
      already_configured: ${{ steps.check.outputs.configured }}
    steps:
      - name: 检查分支保护是否已配置
        id: check
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          if gh api repos/${{ github.repository }}/branches/develop/protection \
             --jq '.required_status_checks.contexts' 2>/dev/null | \
             grep -q "Tests / pre-commit-tests"; then
            echo "configured=true" >> $GITHUB_OUTPUT
            echo "Branch protection already configured"
          else
            echo "configured=false" >> $GITHUB_OUTPUT
            echo "Branch protection not yet configured"
          fi

      - name: 应用分支保护规则
        if: steps.check.outputs.configured == 'false'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cat > /tmp/protection.json << 'EOF'
          {
            "required_status_checks": {
              "strict": true,
              "contexts": ["Tests / pre-commit-tests"]
            },
            "required_pull_request_reviews": {
              "dismiss_stale_reviews": true,
              "require_code_owner_reviews": false,
              "required_approving_review_count": 1,
              "require_last_push_approval": false
            },
            "restrictions": null,
            "required_linear_history": true,
            "allow_force_pushes": false,
            "allow_deletions": false,
            "block_creations": false,
            "required_conversation_resolution": true,
            "enforce_admins": false,
            "required_signatures": false,
            "enabled": true
          }
          EOF
          gh api --method PUT \
            repos/${{ github.repository }}/branches/develop/protection \
            --input /tmp/protection.json
          echo "Branch protection applied successfully"

      - name: 验证保护规则
        if: steps.check.outputs.configured == 'false'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          CONTEXTS=$(gh api repos/${{ github.repository }}/branches/develop/protection \
            --jq '.required_status_checks.contexts[]')
          echo "Required checks:"
          echo "$CONTEXTS"
          echo "$CONTEXTS" | grep -q "Tests / pre-commit-tests" && \
            echo "VERIFIED: Tests / pre-commit-tests is required" || \
            echo "WARNING: Required check not found"
```

### 4.2 方案: 独立初始化工作流

创建 `.github/workflows/init-protection.yml`:

```yaml
name: Initialize Branch Protection

on:
  workflow_dispatch:
    inputs:
      branch:
        description: 'Branch to protect'
        required: false
        default: 'develop'
      required_check:
        description: 'Required status check name'
        required: false
        default: 'Tests / pre-commit-tests'

jobs:
  setup:
    name: 配置分支保护
    runs-on: ubuntu-latest
    permissions:
      contents: read
      administrations: write
    steps:
      - uses: actions/checkout@v4

      - name: Apply branch protection
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          BRANCH: ${{ github.event.inputs.branch }}
          CHECK: ${{ github.event.inputs.required_check }}
        run: |
          echo "Configuring protection for branch: $BRANCH"
          echo "Required check: $CHECK"

          # 检查是否已配置
          if gh api repos/${{ github.repository }}/branches/$BRANCH/protection \
             2>/dev/null; then
            echo "Protection already exists, updating..."
          else
            echo "Creating new protection rule..."
          fi

          # 应用保护规则
          cat > /tmp/protection.json << EOF
          {
            "required_status_checks": {
              "strict": true,
              "contexts": ["$CHECK"]
            },
            "required_pull_request_reviews": {
              "dismiss_stale_reviews": true,
              "require_code_owner_reviews": false,
              "required_approving_review_count": 1,
              "require_last_push_approval": false
            },
            "restrictions": null,
            "required_linear_history": true,
            "allow_force_pushes": false,
            "allow_deletions": false,
            "block_creations": false,
            "required_conversation_resolution": true,
            "enforce_admins": false,
            "required_signatures": false,
            "enabled": true
          }
          EOF

          gh api --method PUT \
            repos/${{ github.repository }}/branches/$BRANCH/protection \
            --input /tmp/protection.json

          echo "Done!"
```

### 4.3 权限要求

CI/CD 中自动配置分支保护需要 **administrations: write** 权限。

在仓库 Settings → Actions → General → Workflow permissions 中:
- 选择 "Read and write permissions"
- 或在具体工作流中声明 `permissions: administrations: write`

> **注意**: `GITHUB_TOKEN` 的默认权限可能不足以配置分支保护。如果自动配置失败，需要:
> 1. 在仓库 Settings → Actions → General 中提升 workflow 权限
> 2. 或创建具有 admin 权限的 Personal Access Token 存为 secret

---

## 五、完整部署验证清单

### 5.1 部署前检查

- [ ] 代码审查 Blocker 问题已修复 (或已记录为已知问题)
- [ ] 本地所有测试通过: `python backend/scripts/pre_commit_tests.py`
- [ ] `.github/workflows/` 目录已提交
- [ ] `requirements.txt` 已更新
- [ ] 无硬编码的密钥或 token 在代码中

### 5.2 部署步骤

```powershell
# Step 1: 创建 GitHub 仓库
gh repo create <REPO_NAME> --public

# Step 2: 添加 remote
cd "c:\Users\Administrator\机械计算小程序"
git remote add origin https://github.com/<OWNER>/<REPO_NAME>.git

# Step 3: 推送代码
git push -u origin master
git checkout -b develop
git push -u origin develop

# Step 4: 应用分支保护
.\backend\scripts\setup_branch_protection.ps1 -Branch develop -AutoConfirm

# Step 5: 验证 CI 触发
gh run list --limit 3

# Step 6: 验证保护规则
gh api repos/<OWNER>/<REPO_NAME>/branches/develop/protection --jq '.required_status_checks'
```

### 5.3 部署后验证

- [ ] GitHub Actions 工作流已触发并成功运行
- [ ] 分支保护规则已生效 (develop 分支)
- [ ] 创建测试 PR 验证 required check 阻断功能
- [ ] 通知团队成员新的合并规则

### 5.4 回滚方案

```powershell
# 删除分支保护规则
gh api --method DELETE "repos/<OWNER>/<REPO_NAME>/branches/develop/protection"

# 删除 remote
git remote remove origin
```

---

## 六、自动化处理建议

### 6.1 gh CLI 安装自动化

```powershell
# Windows (winget)
winget install --id GitHub.cli --accept-source-agreements --accept-package-agreements

# 验证
gh --version

# 非交互认证 (使用 token)
$token = Get-Content -Path ".github-token" -Raw
$token | gh auth login --with-token

# 验证认证
gh auth status
```

### 6.2 首次部署一键脚本

```powershell
<#
.SYNOPSIS
    一键部署: 创建仓库 + 推送代码 + 配置分支保护
#>
param(
    [string]$RepoName = "",
    [string]$Owner = "",
    [switch]$Private = $false
)

$ErrorActionPreference = "Stop"

# 1. 检查 gh CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "[1/6] 安装 gh CLI..." -ForegroundColor Cyan
    winget install --id GitHub.cli --accept-source-agreements --accept-package-agreements
}

# 2. 检查认证
if (-not (gh auth status 2>&1)) {
    Write-Host "[2/6] 认证 GitHub CLI..." -ForegroundColor Cyan
    gh auth login
}

# 3. 创建仓库
$visibility = if ($Private) { "--private" } else { "--public" }
Write-Host "[3/6] 创建仓库..." -ForegroundColor Cyan
gh repo create $RepoName $visibility

# 4. 添加 remote 并推送
Write-Host "[4/6] 推送代码..." -ForegroundColor Cyan
git remote add origin "https://github.com/$Owner/$RepoName.git"
git push -u origin master
git checkout -b develop
git push -u origin develop

# 5. 配置分支保护
Write-Host "[5/6] 配置分支保护..." -ForegroundColor Cyan
.\backend\scripts\setup_branch_protection.ps1 -Branch develop -AutoConfirm

# 6. 验证
Write-Host "[6/6] 验证..." -ForegroundColor Cyan
gh api "repos/$Owner/$RepoName/branches/develop/protection" --jq '.required_status_checks.contexts'

Write-Host ""
Write-Host "部署完成!" -ForegroundColor Green
```

---

## 七、参考链接

- [GitHub Docs: Branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub REST API: Update branch protection](https://docs.github.com/en/rest/branches/branch-protection)
- [gh CLI Manual](https://cli.github.com/manual/)
- [GitHub Actions Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)
