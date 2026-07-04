import json

import pytest

from hook_module_loader import find_hook_module_path, run_hook_subprocess

CODEX_LAUNCH_TOOL_NAME = "mcp__codex__codex"
CODEX_SANDBOX_DOWNGRADE_GUARD_HOOK_SCRIPT_PATH = find_hook_module_path(
    "codex-sandbox-downgrade-guard"
)


def parse_permission_decision(stdout):
    return json.loads(stdout)["hookSpecificOutput"]["permissionDecision"]


class TestCodexSandboxDowngradeGuard:
    @pytest.mark.parametrize(
        "tool_input",
        [
            {"prompt": "x", "sandbox": "read-only"},
            {"prompt": "x", "sandbox": "workspace-write"},
            {"prompt": "x", "approval-policy": "on-request"},
            {"prompt": "x", "approval-policy": "untrusted"},
            {"prompt": "x", "config": {"sandbox_mode": "workspace-write"}},
            {"prompt": "x", "config": {"approval_policy": "on-failure"}},
            {
                "prompt": "x",
                "sandbox": "danger-full-access",
                "config": {"sandbox_mode": "read-only"},
            },
            {"prompt": "x", "sandbox": "read-only", "config": "not-a-dict"},
        ],
    )
    def test_denies_downgraded_codex_launch(
        self, tool_input, invoke_codex_sandbox_downgrade_guard_hook
    ):
        result = invoke_codex_sandbox_downgrade_guard_hook(
            {"tool_name": CODEX_LAUNCH_TOOL_NAME, "tool_input": tool_input}
        )
        assert result.returncode == 0
        assert parse_permission_decision(result.stdout) == "deny"

    @pytest.mark.parametrize(
        "tool_input",
        [
            {"prompt": "x"},
            {"prompt": "x", "sandbox": "danger-full-access"},
            {"prompt": "x", "approval-policy": "never"},
            {
                "prompt": "x",
                "sandbox": "danger-full-access",
                "approval-policy": "never",
            },
            {"prompt": "x", "config": {"sandbox_mode": "danger-full-access"}},
            {"prompt": "x", "config": {"model": "gpt-5.5"}},
            {"prompt": "x", "config": "not-a-dict"},
            {"prompt": "x", "config": 123},
        ],
    )
    def test_allows_full_access_codex_launch(
        self, tool_input, invoke_codex_sandbox_downgrade_guard_hook
    ):
        result = invoke_codex_sandbox_downgrade_guard_hook(
            {"tool_name": CODEX_LAUNCH_TOOL_NAME, "tool_input": tool_input}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    @pytest.mark.parametrize(
        "tool_name",
        ["mcp__codex__codex-reply", "Bash", "Write", "mcp__browser-use__browser_click"],
    )
    def test_ignores_other_tools_even_with_weak_sandbox(
        self, tool_name, invoke_codex_sandbox_downgrade_guard_hook
    ):
        result = invoke_codex_sandbox_downgrade_guard_hook(
            {"tool_name": tool_name, "tool_input": {"sandbox": "read-only"}}
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_ignores_malformed_stdin(self):
        result = run_hook_subprocess(
            CODEX_SANDBOX_DOWNGRADE_GUARD_HOOK_SCRIPT_PATH, "not json"
        )
        assert result.returncode == 0
        assert result.stdout == ""
