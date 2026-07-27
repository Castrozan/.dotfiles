import json

import pytest
from flat_deploy_test_support import (
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)

DISPATCHERS_BY_EVENT_NAME = {
    "PreToolUse": "pre-tool-use-dispatcher.py",
    "PostToolUse": "post-tool-use-dispatcher.py",
    "Stop": "stop-dispatcher.py",
}


@pytest.mark.parametrize("event_name", sorted(DISPATCHERS_BY_EVENT_NAME))
def test_dispatcher_still_runs_when_the_payload_omits_the_event_name(
    tmp_path, event_name
):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)

    blocked = run_flattened_hook(
        runtime_directory,
        DISPATCHERS_BY_EVENT_NAME[event_name],
        {"tool_name": "Bash", "tool_input": {"command": "git add -A"}},
        {"HOME": str(tmp_path), "TMPDIR": str(tmp_path)},
    )
    assert blocked.returncode == 0


def test_pre_tool_use_dispatcher_blocks_without_an_event_name(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)

    blocked = run_flattened_hook(
        runtime_directory,
        "pre-tool-use-dispatcher.py",
        {"tool_name": "Bash", "tool_input": {"command": "git add -A"}},
        {"HOME": str(tmp_path), "TMPDIR": str(tmp_path)},
    )
    assert blocked.returncode == 0
    assert json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"] == (
        "deny"
    )


def test_dispatcher_exits_quietly_on_a_foreign_event_name(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)

    ignored = run_flattened_hook(
        runtime_directory,
        "pre-tool-use-dispatcher.py",
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "git add -A"},
        },
        {"HOME": str(tmp_path), "TMPDIR": str(tmp_path)},
    )
    assert ignored.returncode == 0
    assert ignored.stdout.strip() == ""
