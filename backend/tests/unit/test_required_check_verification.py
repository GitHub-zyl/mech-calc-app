"""
Required Check 验证测试
========================

用途:
    专门用于验证 GitHub Required Status Check 机制是否正常生效。
    当本测试失败时，CI/CD 流水线应报告失败，从而阻止代码合并到 develop 分支。

设计原理:
    - 通过环境变量 REQUIRED_CHECK_VERIFY=1 控制是否启用故意失败
    - 默认情况下 (未设置环境变量) 测试被跳过，不影响正常 CI 运行
    - 当需要验证 required check 机制时，设置环境变量即可触发失败

前置条件:
    1. GitHub 仓库已配置分支保护规则，将 "Tests / required-check-verification" 设为 required status check
    2. 代码已推送到 develop 分支
    3. CI/CD 流水线已正确配置 required-check-verification job

执行步骤:
    1. 设置环境变量 REQUIRED_CHECK_VERIFY=1 (在 CI/CD job 中或本地)
    2. 运行: pytest backend/tests/unit/test_required_check_verification.py -v
    3. 观察测试结果: 应出现 1 个 FAILED

预期结果:
    - 测试失败: assert False (故意触发)
    - CI/CD job "required-check-verification" 状态为 failure
    - GitHub 分支保护阻止 PR 合并 (mergeable_state=blocked)
    - 移除环境变量或修复后，测试通过，合并恢复正常

验证命令 (本地):
    # 触发失败
    REQUIRED_CHECK_VERIFY=1 pytest backend/tests/unit/test_required_check_verification.py -v

    # 正常通过 (不设置环境变量)
    pytest backend/tests/unit/test_required_check_verification.py -v
"""
import os


def test_required_check_mechanism_blocks_merge():
    """
    验证 Required Check 机制能否有效阻断合并操作。

    当环境变量 REQUIRED_CHECK_VERIFY=1 时，本测试故意断言失败，
    用于验证 GitHub 分支保护规则中的 required status check 是否生效。

    预期行为:
        - 设置 REQUIRED_CHECK_VERIFY=1 → 测试失败 → CI job 失败 → 阻止合并
        - 不设置或 REQUIRED_CHECK_VERIFY=0 → 测试跳过 → CI job 成功 → 允许合并
    """
    verify_mode = os.environ.get('REQUIRED_CHECK_VERIFY', '0')

    if verify_mode != '1':
        # 正常模式: 跳过测试，不影响 CI
        # 使用 pytest.skip 而非 pass，确保测试报告中明确标记为 SKIPPED
        import pytest
        pytest.skip(
            "Required check 验证测试已跳过。"
            "设置环境变量 REQUIRED_CHECK_VERIFY=1 可启用故意失败模式，"
            "用于验证分支保护规则是否正常工作。"
        )

    # 故意失败模式: 断言 False，触发测试失败
    # 这将导致 CI job 以非零退出码结束，
    # GitHub 检测到 required status check 失败后阻止 PR 合并
    assert False, (
        "[INTENTIONAL FAILURE] 本测试故意失败，用于验证 Required Check 机制。"
        "如果你看到此消息，说明 required status check 验证机制正常工作。"
        "要恢复正常，请移除环境变量 REQUIRED_CHECK_VERIFY=1 或将其设为 0。"
    )


def test_required_check_environment_variable_format():
    """
    验证 REQUIRED_CHECK_VERIFY 环境变量的合法值。

    确保环境变量只接受 '0' 和 '1' 两个值，其他值应触发警告。
    此测试始终运行（不受 REQUIRED_CHECK_VERIFY 控制）。
    """
    verify_mode = os.environ.get('REQUIRED_CHECK_VERIFY', None)

    if verify_mode is None:
        # 未设置环境变量，正常情况
        return

    # 环境变量已设置，验证其值合法
    assert verify_mode in ('0', '1'), (
        f"REQUIRED_CHECK_VERIFY 环境变量值无效: '{verify_mode}'。"
        f"合法值: '0' (禁用) 或 '1' (启用故意失败模式)。"
        f"请检查 CI/CD 配置或本地环境变量设置。"
    )
