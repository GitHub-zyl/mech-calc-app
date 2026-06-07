#!/usr/bin/env bash
# ============================================================
# setup_branch_protection.sh
#
# 配置 GitHub develop 分支保护规则, 将 pre-commit-tests
# 配置为 required status check.
#
# 平台: Linux / macOS / Git Bash (Windows)
# 前置: gh CLI >= 2.0, gh auth login 完成
# ============================================================

set -e

OWNER="${1:-}"
REPO="${2:-}"
BRANCH="${3:-develop}"

TAG_INFO="INFO"
TAG_OK="OK"
TAG_WARN="WARN"
TAG_ERROR="ERROR"

# 颜色 (仅在 TTY 启用)
if [ -t 1 ]; then
    C_CYAN='\033[36m'
    C_GREEN='\033[32m'
    C_YELLOW='\033[33m'
    C_RED='\033[31m'
    C_RESET='\033[0m'
else
    C_CYAN=''
    C_GREEN=''
    C_YELLOW=''
    C_RED=''
    C_RESET=''
fi

write_info() { echo -e "${C_CYAN}[${TAG_INFO}]${C_RESET} $1"; }
write_ok()   { echo -e "${C_GREEN}[${TAG_OK}]${C_RESET} $1"; }
write_warn() { echo -e "${C_YELLOW}[${TAG_WARN}]${C_RESET} $1"; }
write_err()  { echo -e "${C_RED}[${TAG_ERROR}]${C_RESET} $1"; }

print_line() {
    local char="$1"
    local n="${2:-78}"
    printf '%*s\n' "$n" '' | tr ' ' "$char"
}

# ============================================================
# 标题
# ============================================================
echo -e "${C_CYAN}"
print_line "=" 78
echo "  GitHub Branch Protection Setup (bash)"
print_line "=" 78
echo -e "${C_RESET}"

# ============================================================
# 1. 检查 gh CLI
# ============================================================
if ! command -v gh >/dev/null 2>&1; then
    write_err "gh CLI not found, install:"
    echo "  macOS:   brew install gh"
    echo "  Linux:   sudo apt install gh (Debian/Ubuntu)"
    echo "  Windows: winget install --id GitHub.cli"
    echo "  Download: https://cli.github.com/"
    exit 2
fi
write_info "[1/5] GitHub CLI: $(gh --version | head -n1)"

# ============================================================
# 2. 检查认证
# ============================================================
if ! gh auth status >/dev/null 2>&1; then
    write_err "gh CLI not authenticated, run: gh auth login"
    exit 3
fi
write_info "[2/5] GitHub auth: logged in"

# ============================================================
# 3. 检测 owner/repo
# ============================================================
if [ -z "$OWNER" ] || [ -z "$REPO" ]; then
    NWO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null) || {
        write_err "Cannot auto-detect repo, specify OWNER REPO as arguments"
        exit 4
    }
    OWNER="${NWO%%/*}"
    REPO="${NWO##*/}"
fi
write_info "[3/5] Target repo: $OWNER/$REPO"

# ============================================================
# 4. 检查分支存在
# ============================================================
if ! gh api "repos/$OWNER/$REPO/branches/$BRANCH" >/dev/null 2>&1; then
    write_warn "Branch $BRANCH may not exist or is inaccessible"
    read -r -p "  Continue? (y/N) " ans
    if [ "$ans" != "y" ]; then
        echo "Cancelled"
        exit 5
    fi
fi
write_info "[4/5] Target branch: $BRANCH"

# ============================================================
# 5. 检查 admin 权限
# ============================================================
ADMIN_PERM=$(gh api "repos/$OWNER/$REPO" --jq '.permissions.admin' 2>/dev/null) || {
    write_err "Cannot check permissions"
    exit 6
}
if [ "$ADMIN_PERM" != "true" ]; then
    write_err "Current user lacks admin permission on this repo"
    exit 6
fi
write_info "[5/5] Permission: admin (verified)"

# ============================================================
# 配置预览
# ============================================================
echo
echo -e "${C_CYAN}"
print_line "=" 78
echo "  Configuration Preview"
print_line "=" 78
echo -e "${C_RESET}"
echo "  Branch:              $BRANCH"
echo "  Required Check:      Tests / pre-commit-tests"
echo "  Block failing tests: enabled"
echo "  Required reviews:    1"
echo "  Linear history:      required"
echo "  Allow force push:    no"
echo "  Allow deletion:      no"
echo

# ============================================================
# 构造 JSON payload
# ============================================================
JSON_PAYLOAD=$(cat <<'EOF'
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
  "required_signatures": false,
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "enforce_admins": false,
  "enabled": true
}
EOF
)

# ============================================================
# 用户确认
# ============================================================
read -r -p "  Apply configuration? (y/N) " confirm
if [ "$confirm" != "y" ]; then
    write_info "Cancelled"
    exit 0
fi

# ============================================================
# 调用 API
# ============================================================
echo
echo -e "${C_CYAN}"
print_line "=" 78
echo "  Applying"
print_line "=" 78
echo -e "${C_RESET}"
echo

TMPFILE=$(mktemp)
echo "$JSON_PAYLOAD" > "$TMPFILE"

API_ENDPOINT="repos/$OWNER/$REPO/branches/$BRANCH/protection"
if ! RESPONSE=$(gh api --method PUT "$API_ENDPOINT" --input "$TMPFILE" 2>&1); then
    write_err "Failed: $RESPONSE"
    rm -f "$TMPFILE"
    exit 7
fi
rm -f "$TMPFILE"

write_ok "Branch protection rules applied"
echo
echo "  URL:                  $(echo "$RESPONSE" | grep -oE '"url":\s*"[^"]+"' | head -1 | sed 's/"url":\s*"\(.*\)"/\1/')"
echo "  Strict:               $(echo "$RESPONSE" | grep -oE '"strict":\s*(true|false)' | head -1 | grep -oE '(true|false)')"
echo "  Enforce Admins:       $(echo "$RESPONSE" | grep -oE '"enforce_admins":\s*(true|false)' | head -1 | grep -oE '(true|false)')"
echo

# 显示完整规则
echo -e "${C_CYAN}"
print_line "=" 78
echo "  Current Protection Rules"
print_line "=" 78
echo -e "${C_RESET}"
echo
gh api "$API_ENDPOINT"

echo
echo -e "${C_GREEN}"
print_line "=" 78
write_ok "Configuration complete"
print_line "=" 78
echo -e "${C_RESET}"
echo
echo "  Effect:"
echo "    1. PRs trigger Tests / pre-commit-tests automatically"
echo "    2. Test failure blocks PR merge"
echo "    3. 1+ reviewer approval required"
echo "    4. Linear history enforced (rebase / squash merge)"
echo "    5. Force push and branch deletion blocked"
echo
echo "  Verify:"
echo "    gh api repos/$OWNER/$REPO/branches/$BRANCH/protection"
echo
