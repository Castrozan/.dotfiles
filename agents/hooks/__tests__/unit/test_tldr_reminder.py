import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

HOOKS_ROOT = Path(__file__).resolve().parents[2]
TLDR_REMINDER_HOOK_SCRIPT = next(HOOKS_ROOT.rglob("user-prompt-submit-dispatcher.py"))
REPLY_REMINDER_STATE_MODULE_PATH = next(
    HOOKS_ROOT.rglob("interactive_reply_reminder_state.py")
)

INTERACTIVE_ENV_VAR = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENV_MARKER = "CLAWDE_AGENT_NAME"
REMINDER_STATE_DIRECTORY_ENV_VAR = "INTERACTIVE_REPLY_REMINDER_STATE_DIRECTORY"


def load_reply_reminder_state_module(state_directory: Path):
    os.environ[REMINDER_STATE_DIRECTORY_ENV_VAR] = str(state_directory)
    spec = importlib.util.spec_from_file_location(
        "interactive_reply_reminder_state", REPLY_REMINDER_STATE_MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def invoke_tldr_reminder(
    payload: dict,
    interactive: bool,
    state_directory: Path,
    clawde_background_agent: bool = False,
    clawde_marker_value: str = "",
) -> subprocess.CompletedProcess:
    environment = {
        k: v
        for k, v in os.environ.items()
        if k not in (INTERACTIVE_ENV_VAR, CLAWDE_BACKGROUND_AGENT_ENV_MARKER)
    }
    environment[REMINDER_STATE_DIRECTORY_ENV_VAR] = str(state_directory)
    if interactive:
        environment[INTERACTIVE_ENV_VAR] = "/some/interactive-preferences.md"
    if clawde_background_agent:
        environment[CLAWDE_BACKGROUND_AGENT_ENV_MARKER] = clawde_marker_value
    return subprocess.run(
        [sys.executable, str(TLDR_REMINDER_HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
        env=environment,
    )


def user_prompt_submit_payload(session_id: str) -> dict:
    return {"hook_event_name": "UserPromptSubmit", "session_id": session_id}


def test_injects_reminder_on_first_interactive_prompt_of_session(tmp_path):
    result = invoke_tldr_reminder(
        user_prompt_submit_payload("session-a"),
        interactive=True,
        state_directory=tmp_path,
    )
    parsed = json.loads(result.stdout)
    assert parsed["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "Done:" in parsed["hookSpecificOutput"]["additionalContext"]


def test_suppresses_reminder_after_first_injection_in_same_session(tmp_path):
    first = invoke_tldr_reminder(
        user_prompt_submit_payload("session-b"),
        interactive=True,
        state_directory=tmp_path,
    )
    assert first.stdout.strip() != ""
    second = invoke_tldr_reminder(
        user_prompt_submit_payload("session-b"),
        interactive=True,
        state_directory=tmp_path,
    )
    assert second.stdout.strip() == ""


def test_reinjects_reminder_after_drift_rearm_requested(tmp_path):
    reply_reminder_state = load_reply_reminder_state_module(tmp_path)
    invoke_tldr_reminder(
        user_prompt_submit_payload("session-c"),
        interactive=True,
        state_directory=tmp_path,
    )
    suppressed = invoke_tldr_reminder(
        user_prompt_submit_payload("session-c"),
        interactive=True,
        state_directory=tmp_path,
    )
    assert suppressed.stdout.strip() == ""

    reply_reminder_state.request_reply_reminder_rearm_after_drift("session-c")

    rearmed = invoke_tldr_reminder(
        user_prompt_submit_payload("session-c"),
        interactive=True,
        state_directory=tmp_path,
    )
    assert (
        "Done:" in json.loads(rearmed.stdout)["hookSpecificOutput"]["additionalContext"]
    )


def test_separate_sessions_each_receive_the_first_injection(tmp_path):
    first_session = invoke_tldr_reminder(
        user_prompt_submit_payload("session-d"),
        interactive=True,
        state_directory=tmp_path,
    )
    other_session = invoke_tldr_reminder(
        user_prompt_submit_payload("session-e"),
        interactive=True,
        state_directory=tmp_path,
    )
    assert first_session.stdout.strip() != ""
    assert other_session.stdout.strip() != ""


def test_silent_in_non_interactive_session(tmp_path):
    result = invoke_tldr_reminder(
        user_prompt_submit_payload("session-f"),
        interactive=False,
        state_directory=tmp_path,
    )
    assert result.stdout.strip() == ""


def test_silent_for_clawde_background_agent_even_when_interactive_var_leaked(tmp_path):
    result = invoke_tldr_reminder(
        user_prompt_submit_payload("session-g"),
        interactive=True,
        state_directory=tmp_path,
        clawde_background_agent=True,
        clawde_marker_value="--continue",
    )
    assert result.stdout.strip() == ""


def test_silent_for_clawde_background_agent_with_empty_marker_value(tmp_path):
    result = invoke_tldr_reminder(
        user_prompt_submit_payload("session-h"),
        interactive=True,
        state_directory=tmp_path,
        clawde_background_agent=True,
        clawde_marker_value="",
    )
    assert result.stdout.strip() == ""


def test_silent_on_non_user_prompt_submit_event(tmp_path):
    result = invoke_tldr_reminder(
        {"hook_event_name": "SessionStart", "session_id": "session-i"},
        interactive=True,
        state_directory=tmp_path,
    )
    assert result.stdout.strip() == ""
