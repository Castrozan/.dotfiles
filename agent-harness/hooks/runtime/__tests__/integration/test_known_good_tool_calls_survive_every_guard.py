"""Every deny-emitting PreToolUse guard, run against the known-good corpus.

The dispatcher is invoked whole rather than one guard at a time, so a guard
added later is covered the day it is registered, without anyone remembering to
extend this file. A denial here names the call it broke, which is the piece a
pattern author cannot see from inside their own rule.
"""

import json

import pytest
from hook_module_loader import find_hook_module_path, run_hook_subprocess
from known_good_tool_calls import known_good_tool_calls

PRE_TOOL_USE_DISPATCHER = find_hook_module_path("pre-tool-use-dispatcher")

KNOWN_GOOD_TOOL_CALLS = list(known_good_tool_calls())


def denial_reason_for(tool_call):
    payload = {
        "session_id": "known-good-corpus",
        "transcript_path": "/dev/null",
        "cwd": "/Users/lucas.zanoni/.dotfiles",
        "hook_event_name": "PreToolUse",
        **tool_call,
    }
    completed = run_hook_subprocess(PRE_TOOL_USE_DISPATCHER, json.dumps(payload))
    assert completed.returncode == 0, completed.stderr
    if not completed.stdout.strip():
        return ""
    hook_output = json.loads(completed.stdout)
    hook_specific_output = hook_output.get("hookSpecificOutput", {})
    if hook_specific_output.get("permissionDecision") != "deny":
        return ""
    return hook_specific_output.get("permissionDecisionReason", "denied")


@pytest.mark.parametrize(
    "tool_call",
    [tool_call for _label, tool_call in KNOWN_GOOD_TOOL_CALLS],
    ids=[label for label, _tool_call in KNOWN_GOOD_TOOL_CALLS],
)
def test_a_known_good_tool_call_is_never_denied(tool_call):
    reason = denial_reason_for(tool_call)
    assert reason == "", (
        "a guard denied ordinary work; either the rule is too wide or this call "
        f"does not belong in the corpus: {reason}"
    )
