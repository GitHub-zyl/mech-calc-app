"""apply_branch_protection.py - 无需 gh CLI 的分支保护配置脚本

使用 GitHub REST API + requests 库配置分支保护规则。
适用于 gh CLI 未安装或认证失败的环境。

前置条件:
  1. pip install requests
  2. 设置环境变量:
     - GITHUB_TOKEN: GitHub Personal Access Token (需要 repo 权限)
     - GITHUB_OWNER: 仓库所有者
     - GITHUB_REPO: 仓库名称
  3. Token 生成: https://github.com/settings/tokens

用法:
  # PowerShell
  $env:GITHUB_TOKEN = "ghp_xxxx"
  $env:GITHUB_OWNER = "GitHub-zyl"
  $env:GITHUB_REPO = "机械计算小程序"
  python backend/scripts/apply_branch_protection.py

  # Bash
  export GITHUB_TOKEN="ghp_xxxx"
  export GITHUB_OWNER="GitHub-zyl"
  export GITHUB_REPO="机械计算小程序"
  python backend/scripts/apply_branch_protection.py
"""
import json
import os
import sys

try:
    import requests
except ImportError:
    print("[ERROR] 需要 requests 库: pip install requests")
    sys.exit(2)


def main():
    token = os.getenv("GITHUB_TOKEN", "")
    owner = os.getenv("GITHUB_OWNER", "")
    repo = os.getenv("GITHUB_REPO", "")
    branch = os.getenv("PROTECTION_BRANCH", "develop")
    required_checks = os.getenv("REQUIRED_CHECKS", "Tests / pre-commit-tests,Tests / required-check-verification").split(",")

    # 参数校验
    if not token:
        print("[ERROR] 请设置 GITHUB_TOKEN 环境变量")
        print("  生成方式: https://github.com/settings/tokens")
        print("  所需权限: repo (full control of private repositories)")
        sys.exit(3)
    if not owner or not repo:
        print("[ERROR] 请设置 GITHUB_OWNER 和 GITHUB_REPO 环境变量")
        print("  示例: GITHUB_OWNER=GitHub-zyl GITHUB_REPO=机械计算小程序")
        sys.exit(4)

    api_url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    payload = {
        "required_status_checks": {
            "strict": True,
            "contexts": required_checks,
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

    print("=" * 60)
    print("  GitHub Branch Protection Setup (Python)")
    print("=" * 60)
    print()
    print(f"  仓库:    {owner}/{repo}")
    print(f"  分支:    {branch}")
    print(f"  Checks:  {', '.join(required_checks)}")
    print()

    # 检查是否已配置
    check_resp = requests.get(api_url, headers=headers)
    if check_resp.status_code == 200:
        existing = check_resp.json()
        existing_contexts = existing.get("required_status_checks", {}).get("contexts", [])
        if all(c in existing_contexts for c in required_checks):
            print(f"  [INFO] 分支保护已包含所有 required checks")
            print(f"  当前 contexts: {existing_contexts}")
            print()
            answer = input("  是否覆盖? (y/N): ")
            if answer.lower() != "y":
                print("  已取消")
                return
    elif check_resp.status_code == 404:
        print("  [INFO] 分支保护尚未配置，将创建新规则")
    else:
        print(f"  [WARN] 检查现有规则时返回 {check_resp.status_code}")

    print()
    print("  正在应用分支保护规则...")

    resp = requests.put(api_url, headers=headers, json=payload)

    if resp.status_code == 200:
        data = resp.json()
        print("  [OK] 分支保护规则已应用")
        print()
        rsc = data.get("required_status_checks", {})
        print(f"  Strict:   {rsc.get('strict')}")
        print(f"  Contexts: {rsc.get('contexts')}")
        print(f"  Reviews:  {data.get('required_pull_request_reviews', {}).get('required_approving_review_count')}")
        print()
        print("=" * 60)
        print("  配置完成")
        print("=" * 60)
    elif resp.status_code == 401:
        print("[ERROR] 认证失败: GITHUB_TOKEN 无效或已过期")
        print("  请重新生成: https://github.com/settings/tokens")
        sys.exit(5)
    elif resp.status_code == 403:
        print("[ERROR] 权限不足: token 需要 repo 权限")
        print("  或: 仓库 Settings → Actions → Workflow permissions → Read and write")
        sys.exit(6)
    elif resp.status_code == 404:
        print("[ERROR] 仓库或分支不存在")
        print(f"  请确认: https://github.com/{owner}/{repo}")
        sys.exit(7)
    else:
        print(f"[ERROR] API 返回 {resp.status_code}")
        print(f"  响应: {resp.text[:500]}")
        sys.exit(8)


if __name__ == "__main__":
    main()
