import json

from codex_guard_test_support import (
    COMMAND_GUARD_RUNTIME_SOURCES,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def run_command_guard(tmp_path, payload):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(
        runtime_directory, COMMAND_GUARD_RUNTIME_SOURCES
    )
    return run_flattened_hook(runtime_directory, "prohibited-command-guard.py", payload)


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
    assert result.stdout.strip() == ""


def test_command_guard_allows_a_shell_wrapper_that_only_mentions_the_pattern(tmp_path):
    result = run_command_guard(
        tmp_path,
        {
            "tool_name": "shell",
            "tool_input": {"command": ["bash", "-lc", "echo 'git add -A is banned'"]},
        },
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
