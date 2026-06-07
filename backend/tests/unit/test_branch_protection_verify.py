"""
故意失败的测试用例 - 分支保护验证
====================================

用途:
    专门用于验证 GitHub Required Status Check (pre-commit-tests) 的阻断效果。
    本测试包含一个必然失败的断言，确保 pre-commit-tests 返回非零退出码。

验证目标:
    - pre-commit-tests CI job 必须失败 (exit code != 0)
    - GitHub 分支保护规则必须阻止 PR 合并
    - mergeable_state 必须为 "blocked"
    - 系统必须显示测试失败的具体原因

前置条件:
    1. develop 分支已配置分支保护规则
    2. "Tests / pre-commit-tests" 已设为 required status check
    3. 本文件被 pytest 收集并执行

预期结果:
    - pytest 报告: 1 FAILED
    - CI job "pre-commit-tests": failure
    - PR mergeable_state: blocked
    - GitHub UI 显示: "Merging is blocked"
"""
import sys


def test_intentional_failure_for_branch_protection_verify():
    """
    [INTENTIONAL] 故意失败的测试 - 验证分支保护机制

    失败条件: assert False (无条件失败)
    失败原因: 本测试故意断言 False, 用于验证 required status check 阻断合并
    预期行为: pre-commit-tests 返回非零退出码, PR 被阻止合并

    恢复方式: 删除本文件或从分支中移除即可恢复正常
    """
    # 故意失败: 验证分支保护能否有效阻断合并
    assert False, (
        "[INTENTIONAL FAILURE] 分支保护验证测试 - 故意触发失败。"
        "预期行为: pre-commit-tests CI job 失败, "
        "GitHub 分支保护规则阻止 PR 合并, "
        "mergeable_state 变为 'blocked'。"
        "恢复方式: 删除本测试文件即可。"
    )


def test_environment_info_for_verification_report():
    """
    输出环境信息用于验证报告。

    此测试始终通过, 仅用于记录执行环境。
    """
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("Branch protection verification test executed successfully.")
    assert True
