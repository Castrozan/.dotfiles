import json

import pytest
from hook_module_loader import find_hook_module_path, run_hook_subprocess

PRE_TOOL_USE_DISPATCHER = find_hook_module_path("pre-tool-use-dispatcher")


def dispatched_permission_decision(command):
    payload = {
        "session_id": "merge-request-assignee-guard",
        "transcript_path": "/dev/null",
        "cwd": "/tmp",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    completed = run_hook_subprocess(PRE_TOOL_USE_DISPATCHER, json.dumps(payload))
    assert completed.returncode == 0, completed.stderr
    if not completed.stdout.strip():
        return {}
    return json.loads(completed.stdout).get("hookSpecificOutput", {})


@pytest.mark.parametrize(
    "command, remedy",
    [
        ("glab mr create --fill --yes", "--assignee @me"),
        ("GITLAB_HOST=gitlab.example.com rtk glab mr create --fill", "--assignee @me"),
        ("gh pr create --fill", "--assignee @me"),
        (
            "glab api -X POST projects/1/merge_requests -f source_branch=feature",
            "assignee_id",
        ),
    ],
)
def test_the_dispatcher_denies_a_creation_with_no_assignee(command, remedy):
    decision = dispatched_permission_decision(command)
    assert decision.get("permissionDecision") == "deny", command
    assert remedy in decision.get("permissionDecisionReason", "")


@pytest.mark.parametrize(
    "command",
    [
        "glab mr create --fill --yes --assignee @me",
        "gh pr create --fill --assignee @me",
        "glab api -X POST projects/1/merge_requests -f source_branch=feature "
        "-f assignee_id=42",
        "git push -u origin feature -o merge_request.create",
        "glab mr list",
    ],
)
def test_the_dispatcher_lets_an_assigned_creation_through(command):
    decision = dispatched_permission_decision(command)
    assert decision.get("permissionDecision") != "deny", decision
