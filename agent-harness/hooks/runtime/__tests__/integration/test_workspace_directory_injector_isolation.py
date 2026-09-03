import json
import os
import subprocess
import sys

from conftest import PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH
from hook_module_loader import (
    WORKSPACE_STATE_FILE_ENVIRONMENT_VARIABLE,
    run_hook_subprocess,
)

BASH_LISTING_CALL = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})


def a_workspace_switch_to(directory, tmp_path):
    state_file = tmp_path / "workspace-cwd"
    state_file.write_text(f"{directory}\n")
    return state_file


def test_the_state_file_override_reaches_the_injector_end_to_end(tmp_path):
    state_file = a_workspace_switch_to(tmp_path, tmp_path)
    completed = subprocess.run(
        [sys.executable, str(PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH)],
        input=BASH_LISTING_CALL,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, WORKSPACE_STATE_FILE_ENVIRONMENT_VARIABLE: str(state_file)},
    )
    assert completed.returncode == 0
    rewritten = json.loads(completed.stdout)["hookSpecificOutput"]["updatedInput"]
    assert rewritten["command"].startswith(f"cd {tmp_path}")


def test_the_test_runner_keeps_a_live_workspace_switch_out_of_hook_tests(
    tmp_path, monkeypatch
):
    state_file = a_workspace_switch_to(tmp_path, tmp_path)
    monkeypatch.setenv(WORKSPACE_STATE_FILE_ENVIRONMENT_VARIABLE, str(state_file))
    completed = run_hook_subprocess(
        PRE_TOOL_USE_DISPATCHER_HOOK_SCRIPT_PATH, BASH_LISTING_CALL
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
