import json
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
COMPACTION_HOOK_SCRIPT = next(HOOKS_ROOT.rglob("compaction-context-recovery.py"))


def invoke_compaction_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(COMPACTION_HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_injects_recovery_directive_on_compact_source():
    result = invoke_compaction_hook(
        {"hook_event_name": "SessionStart", "source": "compact"}
    )
    parsed = json.loads(result.stdout)
    additional_context = parsed["hookSpecificOutput"]["additionalContext"]
    assert "POST-COMPACTION RECOVERY" in additional_context
    assert parsed["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_silent_on_startup_source():
    result = invoke_compaction_hook(
        {"hook_event_name": "SessionStart", "source": "startup"}
    )
    assert result.stdout.strip() == ""


def test_silent_on_resume_source():
    result = invoke_compaction_hook(
        {"hook_event_name": "SessionStart", "source": "resume"}
    )
    assert result.stdout.strip() == ""


def test_silent_on_non_session_start_event():
    result = invoke_compaction_hook(
        {"hook_event_name": "PreToolUse", "source": "compact"}
    )
    assert result.stdout.strip() == ""
