import json
import subprocess
import sys
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

HOOKS_ROOT = Path(__file__).resolve().parents[2]
SESSION_START_DISPATCHER_SCRIPT = next(HOOKS_ROOT.rglob("session-start-dispatcher.py"))


def invoke_session_start_dispatcher(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SESSION_START_DISPATCHER_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )


def test_concatenates_session_context_then_recovery_on_compact_source():
    result = invoke_session_start_dispatcher(
        {"hook_event_name": "SessionStart", "source": "compact"}
    )
    parsed = json.loads(result.stdout)
    additional_context = parsed["hookSpecificOutput"]["additionalContext"]
    assert parsed["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "SESSION CONTEXT" in additional_context
    assert "POST-COMPACTION RECOVERY" in additional_context
    assert additional_context.index("SESSION CONTEXT") < additional_context.index(
        "POST-COMPACTION RECOVERY"
    )


def test_recovery_directive_absent_on_startup_source():
    result = invoke_session_start_dispatcher(
        {"hook_event_name": "SessionStart", "source": "startup"}
    )
    assert "POST-COMPACTION RECOVERY" not in result.stdout


def test_recovery_directive_absent_on_resume_source():
    result = invoke_session_start_dispatcher(
        {"hook_event_name": "SessionStart", "source": "resume"}
    )
    assert "POST-COMPACTION RECOVERY" not in result.stdout


def test_silent_on_non_session_start_event():
    result = invoke_session_start_dispatcher(
        {"hook_event_name": "PreToolUse", "source": "compact"}
    )
    assert result.stdout.strip() == ""
