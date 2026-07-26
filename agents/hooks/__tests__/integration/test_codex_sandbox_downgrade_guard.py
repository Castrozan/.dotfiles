import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

codex_sandbox_downgrade_guard_handler = import_hyphenated_hook_module(
    "codex_sandbox_downgrade_guard_handler"
)

CODEX_LAUNCH_TOOL_NAME = "mcp__codex__codex"


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
    def test_denies_downgraded_codex_launch(self, tool_input):
        result = codex_sandbox_downgrade_guard_handler.handle(
            {"tool_name": CODEX_LAUNCH_TOOL_NAME, "tool_input": tool_input}
        )
        assert result is not None
        assert result.decision == "deny"

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
    def test_allows_full_access_codex_launch(self, tool_input):
        result = codex_sandbox_downgrade_guard_handler.handle(
            {"tool_name": CODEX_LAUNCH_TOOL_NAME, "tool_input": tool_input}
        )
        assert result is None

    @pytest.mark.parametrize(
        "tool_name",
        ["mcp__codex__codex-reply", "Bash", "Write", "mcp__browser-use__browser_click"],
    )
    def test_ignores_other_tools_even_with_weak_sandbox(self, tool_name):
        result = codex_sandbox_downgrade_guard_handler.handle(
            {"tool_name": tool_name, "tool_input": {"sandbox": "read-only"}}
        )
        assert result is None

    def test_ignores_input_without_a_tool_input(self):
        result = codex_sandbox_downgrade_guard_handler.handle(
            {"tool_name": CODEX_LAUNCH_TOOL_NAME}
        )
        assert result is None
