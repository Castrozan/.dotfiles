import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
TLDR_REMINDER_HOOK_SCRIPT = next(HOOKS_ROOT.rglob("tldr-reminder.py"))

INTERACTIVE_ENV_VAR = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENV_MARKER = "CLAWDE_RESUME_FLAG"


def invoke_tldr_reminder(
    payload: dict,
    interactive: bool,
    clawde_background_agent: bool = False,
    clawde_marker_value: str = "",
) -> subprocess.CompletedProcess:
    environment = {
        k: v
        for k, v in os.environ.items()
        if k not in (INTERACTIVE_ENV_VAR, CLAWDE_BACKGROUND_AGENT_ENV_MARKER)
    }
    if interactive:
        environment[INTERACTIVE_ENV_VAR] = "/some/interactive-preferences.md"
    if clawde_background_agent:
        environment[CLAWDE_BACKGROUND_AGENT_ENV_MARKER] = clawde_marker_value
    return subprocess.run(
        [sys.executable, str(TLDR_REMINDER_HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        env=environment,
    )


def test_injects_reminder_in_interactive_session():
    result = invoke_tldr_reminder(
        {"hook_event_name": "UserPromptSubmit"}, interactive=True
    )
    parsed = json.loads(result.stdout)
    assert parsed["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "Done:" in parsed["hookSpecificOutput"]["additionalContext"]


def test_silent_in_non_interactive_session():
    result = invoke_tldr_reminder(
        {"hook_event_name": "UserPromptSubmit"}, interactive=False
    )
    assert result.stdout.strip() == ""


def test_silent_for_clawde_background_agent_even_when_interactive_var_leaked():
    result = invoke_tldr_reminder(
        {"hook_event_name": "UserPromptSubmit"},
        interactive=True,
        clawde_background_agent=True,
        clawde_marker_value="--continue",
    )
    assert result.stdout.strip() == ""


def test_silent_for_clawde_background_agent_with_empty_marker_value():
    result = invoke_tldr_reminder(
        {"hook_event_name": "UserPromptSubmit"},
        interactive=True,
        clawde_background_agent=True,
        clawde_marker_value="",
    )
    assert result.stdout.strip() == ""


def test_silent_on_non_user_prompt_submit_event():
    result = invoke_tldr_reminder({"hook_event_name": "SessionStart"}, interactive=True)
    assert result.stdout.strip() == ""
