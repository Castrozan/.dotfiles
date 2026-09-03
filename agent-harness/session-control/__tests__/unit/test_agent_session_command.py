import os
import subprocess
from pathlib import Path

import pytest

COMMAND = Path(__file__).resolve().parents[2] / "agent-session"
CONTINUATION_PROMPT = "This session was restarted. Continue from where you left off."


def run_command(tmp_path, arguments, environment=None):
    herdr = tmp_path / "herdr"
    herdr.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n", encoding="utf-8")
    herdr.chmod(0o755)
    command_environment = os.environ.copy()
    command_environment.pop("CLAWDE_AGENT_NAME", None)
    command_environment.update(
        {
            "HERDR_PANE_ID": "w1:p2",
            "PATH": f"{tmp_path}:{command_environment['PATH']}",
        }
    )
    command_environment.update(environment or {})
    return subprocess.run(
        ["bash", str(COMMAND), *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=command_environment,
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


def test_exit_delegates_self_lifecycle_to_herdr(tmp_path):
    result = run_command(tmp_path, ["exit"])

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["agent", "exit"]


def test_print_target_resolves_the_callers_herdr_pane(tmp_path):
    result = run_command(tmp_path, ["exit", "--print-target"])

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["agent", "get", "w1:p2"]


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


def test_lifecycle_requires_the_callers_herdr_pane(tmp_path):
    result = run_command(tmp_path, ["restart"], {"HERDR_PANE_ID": ""})

    assert result.returncode == 1
    assert "Herdr pane" in result.stderr
    assert result.stdout == ""
