import json
import subprocess
import sys

import pytest
from hook_module_loader import (
    HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    environment_isolated_from_the_machine_workspace_switch,
    find_hook_module_path,
)

PRE_TOOL_USE_DISPATCHER = find_hook_module_path("pre-tool-use-dispatcher")

WAITS_THAT_PARK_THE_FOREGROUND = [
    "herdr agent wait w1K:p4 --until idle --until done --timeout 580000 2>&1 | tail -2",
    "herdr agent wait w1K:p4 --until done",
    "cd /tmp && herdr agent wait w1:p2 --timeout $WAIT_MILLISECONDS",
    "herdr pane wait-output w4E:p6 --match REVIEW-DONE --timeout 600000",
    "wait-for-event process 4166743; cat /tmp/lint.exit",
    "timeout 40 wait-for-event process 4043170; tail -15 /tmp/connect.log",
    "wait-for-event file /tmp/rebuild.log --match REBUILD_EXIT= --timeout-seconds 900",
    "hypruse wait_for window_open --match Steam --timeout 60",
    "docker wait build-container",
    'ci-watcher 46077434723; echo "exit=$?"',
    "timeout 20 ci-watcher 46077434723 --repo https://github.com/example/project",
]

BOUNDED_SYNCHRONIZATIONS_AND_MENTIONS = [
    "herdr pane wait-output w4E:p6 --match READY --timeout 5000",
    "herdr agent wait w4E:p6 --until working --timeout=30000",
    "timeout 20 wait-for-event process 4030397; cat /tmp/summon.log",
    "wait-for-event file /tmp/server.log --match listening --timeout-seconds 15",
    "hypruse wait_for window_open --match Steam",
    "timeout 10 docker wait build-container",
    "ci-watcher --help",
    "echo 'run herdr agent wait in the background'",
    "cat > /tmp/note.txt <<'EOF'\nwait-for-event process 1\nEOF",
]


def pre_tool_use_output(command_string, run_in_background, surface="claude"):
    payload = {
        "session_id": "foreground-event-wait",
        "transcript_path": "/dev/null",
        "cwd": "/Users/lucas.zanoni/.dotfiles",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": command_string,
            "run_in_background": run_in_background,
        },
    }
    completed = subprocess.run(
        [sys.executable, str(PRE_TOOL_USE_DISPATCHER), f"--surface={surface}"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
        env=environment_isolated_from_the_machine_workspace_switch(),
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout or "{}").get("hookSpecificOutput", {})


@pytest.mark.parametrize("command_string", WAITS_THAT_PARK_THE_FOREGROUND)
def test_a_wait_that_parks_the_session_is_denied_only_in_the_foreground(
    command_string,
):
    backgrounded = pre_tool_use_output(command_string, run_in_background=True)
    foreground = pre_tool_use_output(command_string, run_in_background=False)

    assert backgrounded.get("permissionDecision") != "deny"
    assert foreground.get("permissionDecision") == "deny"
    reason = foreground["permissionDecisionReason"]
    assert "(foreground-event-wait)" in reason
    assert "run_in_background" in reason
    assert "background-bash-anti-patterns.md" in reason
    assert len(reason) <= 400


@pytest.mark.parametrize("command_string", BOUNDED_SYNCHRONIZATIONS_AND_MENTIONS)
def test_a_short_bounded_synchronization_stays_in_the_foreground(command_string):
    foreground = pre_tool_use_output(command_string, run_in_background=False)

    assert foreground.get("permissionDecision") != "deny"


@pytest.mark.parametrize("surface", ["codex", "opencode", "hermes", "pi"])
def test_a_harness_without_background_execution_keeps_its_foreground_waits(surface):
    foreground = pre_tool_use_output(
        "herdr agent wait w1K:p4 --until done", False, surface
    )

    assert foreground.get("permissionDecision") != "deny"
