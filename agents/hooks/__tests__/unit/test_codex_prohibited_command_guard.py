import json

from codex_guard_test_support import (
    permission_decision_of,
    run_codex_pre_tool_use_dispatcher,
)


def run_command_guard(tmp_path, payload):
    return run_codex_pre_tool_use_dispatcher(tmp_path, payload)


def test_command_guard_blocks_codex_shell_git_add_all(tmp_path):
    result = run_command_guard(
        tmp_path,
        {"tool_name": "shell", "tool_input": {"command": ["git", "add", "-A"]}},
    )
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "BLOCKED" in blocked["systemMessage"]


def test_command_guard_blocks_git_add_all_inside_a_shell_wrapper(tmp_path):
    result = run_command_guard(
        tmp_path,
        {
            "tool_name": "shell",
            "tool_input": {"command": ["bash", "-lc", "echo staging\ngit add -A"]},
        },
    )
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_command_guard_allows_codex_read_only_shell(tmp_path):
    result = run_command_guard(
        tmp_path,
        {"tool_name": "shell", "tool_input": {"command": ["cat", "README.md"]}},
    )
    assert result.returncode == 0
    assert permission_decision_of(result) is None


def test_command_guard_allows_a_shell_wrapper_that_only_mentions_the_pattern(tmp_path):
    result = run_command_guard(
        tmp_path,
        {
            "tool_name": "shell",
            "tool_input": {"command": ["bash", "-lc", "echo 'git add -A is banned'"]},
        },
    )
    assert result.returncode == 0
    assert permission_decision_of(result) is None
