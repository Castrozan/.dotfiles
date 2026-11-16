import json

import pytest
from hook_module_loader import find_hook_module_path, run_hook_subprocess
from known_silent_background_waits import known_silent_background_wait_tool_calls

PRE_TOOL_USE_DISPATCHER = find_hook_module_path("pre-tool-use-dispatcher")

KNOWN_SILENT_BACKGROUND_WAIT_TOOL_CALLS = list(
    known_silent_background_wait_tool_calls()
)


def permission_decision_for(tool_call):
    payload = {
        "session_id": "known-silent-background-waits",
        "transcript_path": "/dev/null",
        "cwd": "/Users/lucas.zanoni/.dotfiles",
        "hook_event_name": "PreToolUse",
        **tool_call,
    }
    completed = run_hook_subprocess(PRE_TOOL_USE_DISPATCHER, json.dumps(payload))
    assert completed.returncode == 0, completed.stderr
    if not completed.stdout.strip():
        return {}
    return json.loads(completed.stdout).get("hookSpecificOutput", {})


@pytest.mark.parametrize(
    ("tool_call", "denied_by"),
    [
        (tool_call, denied_by)
        for _label, tool_call, denied_by in KNOWN_SILENT_BACKGROUND_WAIT_TOOL_CALLS
    ],
    ids=[
        label
        for label, _tool_call, _denied_by in KNOWN_SILENT_BACKGROUND_WAIT_TOOL_CALLS
    ],
)
def test_a_background_wait_that_went_silent_is_denied_by_its_rule(tool_call, denied_by):
    hook_decision = permission_decision_for(tool_call)

    assert hook_decision.get("permissionDecision") == "deny", (
        "a background wait that sat silent in a real session is allowed again; "
        "tighten background_wait_shape_classifier until it is denied"
    )
    assert denied_by in hook_decision.get("permissionDecisionReason", "")
