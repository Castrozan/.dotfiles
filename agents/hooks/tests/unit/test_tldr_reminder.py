import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
TLDR_REMINDER_HOOK_SCRIPT = next(HOOKS_ROOT.rglob("tldr-reminder.py"))

INTERACTIVE_ENV_VAR = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"


def invoke_tldr_reminder(
    payload: dict, interactive: bool
) -> subprocess.CompletedProcess:
    environment = {k: v for k, v in os.environ.items() if k != INTERACTIVE_ENV_VAR}
    if interactive:
        environment[INTERACTIVE_ENV_VAR] = "/some/interactive-preferences.md"
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


def test_silent_on_non_user_prompt_submit_event():
    result = invoke_tldr_reminder({"hook_event_name": "SessionStart"}, interactive=True)
    assert result.stdout.strip() == ""
