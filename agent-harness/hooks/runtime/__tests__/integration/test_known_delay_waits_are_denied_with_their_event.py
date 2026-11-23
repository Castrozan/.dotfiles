import json
import subprocess
import sys

import pytest
from hook_module_loader import (
    HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    environment_isolated_from_the_machine_workspace_switch,
    find_hook_module_path,
)
from known_delay_waits import known_delay_wait_tool_calls
from wait_target_event_replacements import EVENT_REPLACEMENT_BY_WAIT_TARGET

PRE_TOOL_USE_DISPATCHER = find_hook_module_path("pre-tool-use-dispatcher")
KNOWN_DELAY_WAIT_TOOL_CALLS = list(known_delay_wait_tool_calls())
CI_POLL = "until gh run view 1 --json conclusion | grep -q success; do sleep 20; done"


def pre_tool_use_output(tool_call, surface="claude"):
    payload = {
        "session_id": "known-delay-waits",
        "transcript_path": "/dev/null",
        "cwd": "/Users/lucas.zanoni/.dotfiles",
        "hook_event_name": "PreToolUse",
        **tool_call,
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


@pytest.mark.parametrize(
    ("tool_call", "rule_on_target"),
    [(tool_call, rule) for _label, tool_call, rule in KNOWN_DELAY_WAIT_TOOL_CALLS],
    ids=[label for label, _tool_call, _rule in KNOWN_DELAY_WAIT_TOOL_CALLS],
)
def test_a_mined_delay_wait_is_denied_naming_the_event_to_wait_on(
    tool_call, rule_on_target
):
    hook_output = pre_tool_use_output(tool_call)
    reason = hook_output.get("permissionDecisionReason", "")
    target_name = rule_on_target.rsplit(" on ", 1)[1]
    assert hook_output.get("permissionDecision") == "deny"
    assert f"({rule_on_target})" in reason
    assert reason.endswith(EVENT_REPLACEMENT_BY_WAIT_TARGET[target_name])


@pytest.mark.parametrize("surface", ["claude", "codex", "opencode", "hermes", "pi"])
def test_every_surface_denies_a_foreground_ci_poll(surface):
    tool_call = {"tool_name": "Bash", "tool_input": {"command": CI_POLL}}
    hook_output = pre_tool_use_output(tool_call, surface)
    assert hook_output.get("permissionDecision") == "deny"
    assert "ci-watcher" in hook_output.get("permissionDecisionReason", "")


def test_a_codex_shell_call_is_denied_after_normalization():
    tool_call = {
        "tool_name": "shell",
        "tool_input": {"command": ["bash", "-lc", CI_POLL]},
    }
    hook_output = pre_tool_use_output(tool_call, "codex")
    assert hook_output.get("permissionDecision") == "deny"
    assert "sleep-paced-loop on ci-run" in hook_output["permissionDecisionReason"]
