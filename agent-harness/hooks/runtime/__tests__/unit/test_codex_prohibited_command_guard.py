import json

import pytest

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


@pytest.mark.parametrize(
    "command",
    [
        ["./repository/verification/run.sh", "--quick"],
        ["bash", "-lc", "./repository/verification/run.sh --quick"],
        ["bash", "-lc", "./repository/verification/'run.sh' --quick"],
        ["bash", "-lc", "./repository/verification/$'run.sh' --quick"],
        [
            "bash",
            "-lc",
            "cd repository/verification; ./`printf run`.`printf sh` --quick",
        ],
        [
            "bash",
            "-lc",
            "directory=repository/verification; runner=run.sh; ./$directory/$runner --quick",
        ],
        [
            "bash",
            "-lc",
            "directory=repository/verification; runner=run; extension=sh; ./$directory/$runner.$extension --quick",
        ],
        [
            "bash",
            "-lc",
            "directory='repository/verification'; runner=run; extension=sh; ./$directory/$runner.$extension --quick",
        ],
    ],
)
def test_command_guard_blocks_codex_test_runner_invocations(tmp_path, command):
    result = run_command_guard(
        tmp_path,
        {"tool_name": "shell", "tool_input": {"command": command}},
    )
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "repository/verification/run.sh" in blocked["systemMessage"]


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


@pytest.mark.parametrize(
    "command",
    [
        ["pytest", "agent-harness/quality/evaluations/__tests__/unit"],
        ["pytest", "agent-harness/quality/evaluations/__tests__/unit/"],
        ["pytest", "agent-harness/quality/evaluations/integration"],
        ["pytest", "agent-harness/quality/evaluations"],
        ["pytest"],
        ["pytest", "."],
        ["nix", "flake", "check"],
    ],
)
def test_command_guard_blocks_codex_ci_owned_suite_runs(tmp_path, command):
    result = run_command_guard(
        tmp_path,
        {"tool_name": "shell", "tool_input": {"command": command}},
    )
    assert result.returncode == 0
    blocked = json.loads(result.stdout)
    assert blocked["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_command_guard_allows_codex_info_flags(tmp_path):
    result = run_command_guard(
        tmp_path,
        {"tool_name": "shell", "tool_input": {"command": ["pytest", "--version"]}},
    )
    assert result.returncode == 0
    assert permission_decision_of(result) is None


def test_command_guard_allows_codex_targeted_test_file(tmp_path):
    result = run_command_guard(
        tmp_path,
        {
            "tool_name": "shell",
            "tool_input": {
                "command": [
                    "pytest",
                    "agent-harness/quality/evaluations/__tests__/unit/test_run_evals_baseline.py",
                ]
            },
        },
    )
    assert result.returncode == 0
    assert permission_decision_of(result) is None
