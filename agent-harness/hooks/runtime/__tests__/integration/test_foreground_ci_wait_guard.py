"""A foreground wait on CI parks the agent for the length of the run.

`gh run watch` blocks until the run finishes, which is minutes, and every
progress redraw it prints lands in the agent's context. The agent cannot do
anything else while it waits, so the whole run is dead time bought with
tokens. The command is fine backgrounded, where the harness notifies on exit,
so the guard denies only the foreground shape.

Paired the way the read-only inspection cases are: allowed shapes first, then
the shapes that must stay denied, so a later widening of the pattern cannot
quietly take the allowed ones with it.
"""

import json

import pytest
from hook_module_loader import find_hook_module_path, run_hook_subprocess

PRE_TOOL_USE_DISPATCHER = find_hook_module_path("pre-tool-use-dispatcher")

COMMANDS_THAT_MUST_STAY_ALLOWED_IN_THE_FOREGROUND = [
    "gh run list --commit abc123 --json name,conclusion",
    "gh run view 30957498339 --log-failed",
    "gh pr checks 42",
    "gh run watch --help",
    "grep -rn 'gh run watch' agent-harness/hooks/runtime",
    "echo 'use gh run watch in the background'",
    "rg 'gh run watch' --files-with-matches",
    "gh api repos/Castrozan/.dotfiles/actions/runs",
    "for sha in a1 b2; do gh run list --commit $sha --json conclusion; done",
    "for i in $(seq 1 5); do curl -sS localhost:8080/health; sleep 5; done",
    "gh run list --json conclusion && sleep 5 && gh run list --json conclusion",
]

COMMANDS_THAT_MUST_BE_DENIED_IN_THE_FOREGROUND = [
    "gh run watch 30957498339",
    "gh run watch 30957498339 --exit-status",
    "gh run watch $(gh run list --json databaseId -q '.[0].databaseId')",
    "gh pr checks 42 --watch",
    "gh pr checks --watch --fail-fast",
    "cd /tmp && gh run watch 123",
    "gh run watch 123 >/dev/null 2>&1; echo done",
    (
        "for i in $(seq 1 25); do out=$(gh run list --commit abc --json conclusion); "
        'if [ -n "$out" ]; then echo "$out"; exit 0; fi; sleep 40; done'
    ),
    "while true; do gh run view 123 --json conclusion; sleep 30; done",
    "until gh pr checks 42 | grep -q pass; do sleep 20; done",
]


def run_pre_tool_use(command_string, run_in_background):
    payload = {
        "session_id": "foreground-ci-wait",
        "transcript_path": "/dev/null",
        "cwd": "/Users/lucas.zanoni/.dotfiles",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": command_string,
            "run_in_background": run_in_background,
        },
    }
    completed = run_hook_subprocess(PRE_TOOL_USE_DISPATCHER, json.dumps(payload))
    assert completed.returncode == 0, completed.stderr
    if not completed.stdout.strip():
        return ""
    hook_output = json.loads(completed.stdout)
    specific = hook_output.get("hookSpecificOutput", {})
    return specific.get("permissionDecision", "")


@pytest.mark.parametrize(
    "command_string", COMMANDS_THAT_MUST_STAY_ALLOWED_IN_THE_FOREGROUND
)
def test_reading_about_a_run_is_not_waiting_on_one(command_string):
    assert run_pre_tool_use(command_string, run_in_background=False) != "deny"


@pytest.mark.parametrize(
    "command_string", COMMANDS_THAT_MUST_BE_DENIED_IN_THE_FOREGROUND
)
def test_waiting_on_ci_in_the_foreground_is_denied(command_string):
    assert run_pre_tool_use(command_string, run_in_background=True) != "deny"
    assert run_pre_tool_use(command_string, run_in_background=False) == "deny"


@pytest.mark.parametrize(
    "command_string",
    [
        "gh run watch 123",
        "while true; do gh run view 1 --json conclusion; sleep 30; done",
    ],
)
def test_the_denial_points_at_the_reference_file_rather_than_inlining_it(
    command_string,
):
    payload = {
        "session_id": "foreground-ci-wait",
        "transcript_path": "/dev/null",
        "cwd": "/Users/lucas.zanoni/.dotfiles",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command_string, "run_in_background": False},
    }
    completed = run_hook_subprocess(PRE_TOOL_USE_DISPATCHER, json.dumps(payload))
    reason = json.loads(completed.stdout)["hookSpecificOutput"][
        "permissionDecisionReason"
    ]
    assert "background-bash-anti-patterns.md" in reason
    assert len(reason) <= 400, (
        "a deny reason states what is blocked and points at the file carrying the "
        f"detail; this one runs to {len(reason)} characters and is teaching instead"
    )
