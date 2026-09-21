import json

import pytest

from agent_session_command_runner import (
    CONTINUATION_PROMPT,
    agent_response,
    run_command,
)


def test_restart_delegates_self_lifecycle_to_herdr(tmp_path):
    result = run_command(tmp_path, ["restart"])

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "agent",
        "restart",
        "--prompt",
        CONTINUATION_PROMPT,
    ]
    assert (tmp_path / "herdr-calls").read_text(encoding="utf-8").splitlines() == [
        "agent get w1:p2",
        f"agent restart --prompt {CONTINUATION_PROMPT}",
    ]


def test_restart_refuses_an_unsaved_codex_session_before_calling_herdr(tmp_path):
    result = run_command(tmp_path, ["restart"], persist_session=False)

    assert result.returncode == 1
    assert "has no saved rollout" in result.stderr
    assert "left untouched" in result.stderr
    assert (tmp_path / "herdr-calls").read_text(encoding="utf-8").splitlines() == [
        "agent get w1:p2"
    ]


def test_restart_refuses_a_target_that_differs_from_the_running_codex_session(
    tmp_path,
):
    result = run_command(
        tmp_path,
        ["restart"],
        {"CODEX_THREAD_ID": "01a0840b-752f-7d60-b58d-7fe21ffa3761"},
    )

    assert result.returncode == 1
    assert "but the running Codex session is" in result.stderr
    assert (tmp_path / "herdr-calls").read_text(encoding="utf-8").splitlines() == [
        "agent get w1:p2"
    ]


def test_restart_preserves_non_codex_lifecycle_behavior(tmp_path):
    result = run_command(
        tmp_path,
        ["restart"],
        {"HERDR_AGENT_RESPONSE": agent_response("claude", "claude-session")},
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "agent",
        "restart",
        "--prompt",
        CONTINUATION_PROMPT,
    ]


def test_exit_delegates_self_lifecycle_to_herdr(tmp_path):
    result = run_command(tmp_path, ["exit"])

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["agent", "exit"]


def test_print_target_resolves_the_callers_herdr_pane(tmp_path):
    result = run_command(tmp_path, ["exit", "--print-target"])

    assert result.returncode == 0
    assert json.loads(result.stdout)["result"]["agent"]["agent"] == "codex"


@pytest.mark.parametrize("operation", ["restart", "exit"])
def test_clawde_owned_sessions_refuse_direct_lifecycle(tmp_path, operation):
    result = run_command(
        tmp_path,
        [operation],
        {"CLAWDE_AGENT_NAME": "steward"},
    )

    assert result.returncode == 1
    assert "Clawde-managed" in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("operation", ["restart", "compact", "exit"])
def test_every_operation_requires_the_callers_herdr_pane(tmp_path, operation):
    result = run_command(tmp_path, [operation], {"HERDR_PANE_ID": ""})

    assert result.returncode == 1
    assert "Herdr pane" in result.stderr
    assert result.stdout == ""
