import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
RECORD_HOOK_SCRIPT = next(HOOKS_ROOT.rglob("record-edited-source-file.py"))
TURN_REVIEW_HOOK_SCRIPT = next(HOOKS_ROOT.rglob("lint-turn-review.py"))

sys.path.insert(0, str(HOOKS_ROOT / "lint"))

from lint_ledger import (  # noqa: E402
    append_edited_source_file,
    ledger_file_path_for_session,
    read_and_clear_edited_source_files,
)


def run_hook(script: Path, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )


def clear_session_ledger(session_id: str) -> None:
    try:
        os.remove(ledger_file_path_for_session(session_id))
    except OSError:
        pass


def test_records_lintable_file(tmp_path):
    session_id = "pytest-record-lintable"
    clear_session_ledger(session_id)
    python_file = tmp_path / "module.py"
    python_file.write_text("value = 1\n")
    run_hook(
        RECORD_HOOK_SCRIPT,
        {"tool_input": {"file_path": str(python_file)}, "session_id": session_id},
    )
    assert read_and_clear_edited_source_files(session_id) == [str(python_file)]


def test_ignores_non_lintable_file(tmp_path):
    session_id = "pytest-record-nonlintable"
    clear_session_ledger(session_id)
    markdown_file = tmp_path / "notes.md"
    markdown_file.write_text("hello\n")
    run_hook(
        RECORD_HOOK_SCRIPT,
        {"tool_input": {"file_path": str(markdown_file)}, "session_id": session_id},
    )
    assert read_and_clear_edited_source_files(session_id) == []


def test_turn_review_suggests_repo_native_command(tmp_path):
    session_id = "pytest-turn-review-native"
    clear_session_ledger(session_id)
    (tmp_path / "package.json").write_text('{"scripts": {"lint": "eslint ."}}')
    typescript_file = tmp_path / "app.ts"
    typescript_file.write_text("const a = 1\n")
    append_edited_source_file(session_id, str(typescript_file))
    result = run_hook(
        TURN_REVIEW_HOOK_SCRIPT,
        {"hook_event_name": "Stop", "session_id": session_id},
    )
    parsed = json.loads(result.stdout)
    assert "npm run lint" in parsed["systemMessage"]


def test_turn_review_suggests_linter_when_no_native_command(tmp_path):
    session_id = "pytest-turn-review-fallback"
    clear_session_ledger(session_id)
    python_file = tmp_path / "module.py"
    python_file.write_text("value = 1\n")
    append_edited_source_file(session_id, str(python_file))
    result = run_hook(
        TURN_REVIEW_HOOK_SCRIPT,
        {"hook_event_name": "Stop", "session_id": session_id},
    )
    parsed = json.loads(result.stdout)
    assert "ruff" in parsed["systemMessage"]


def test_turn_review_handles_subagent_stop_event(tmp_path):
    session_id = "pytest-turn-review-subagent"
    clear_session_ledger(session_id)
    (tmp_path / "package.json").write_text('{"scripts": {"lint": "eslint ."}}')
    typescript_file = tmp_path / "app.ts"
    typescript_file.write_text("const a = 1\n")
    append_edited_source_file(session_id, str(typescript_file))
    result = run_hook(
        TURN_REVIEW_HOOK_SCRIPT,
        {"hook_event_name": "SubagentStop", "session_id": session_id},
    )
    parsed = json.loads(result.stdout)
    assert "npm run lint" in parsed["systemMessage"]


def test_turn_review_silent_when_no_files_recorded():
    session_id = "pytest-turn-review-empty"
    clear_session_ledger(session_id)
    result = run_hook(
        TURN_REVIEW_HOOK_SCRIPT,
        {"hook_event_name": "Stop", "session_id": session_id},
    )
    assert result.stdout.strip() == ""


def test_turn_review_silent_on_non_stop_event(tmp_path):
    session_id = "pytest-turn-review-wrong-event"
    clear_session_ledger(session_id)
    append_edited_source_file(session_id, str(tmp_path / "x.py"))
    result = run_hook(
        TURN_REVIEW_HOOK_SCRIPT,
        {"hook_event_name": "PreToolUse", "session_id": session_id},
    )
    assert result.stdout.strip() == ""
    clear_session_ledger(session_id)
