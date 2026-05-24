import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIRECTORY = Path(__file__).resolve().parent.parent.parent
END_OF_WORK_COMPLIANCE_REVIEW_HOOK_SCRIPT_PATH = next(
    HOOKS_DIRECTORY.rglob("end-of-work-compliance-review.py")
)


@pytest.fixture
def invoke_end_of_work_compliance_review_hook():
    def runner(payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(END_OF_WORK_COMPLIANCE_REVIEW_HOOK_SCRIPT_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=10,
        )

    return runner


class TestStopHookActiveGuard:
    def test_exits_zero_without_blocking_when_stop_hook_active_is_true(
        self, invoke_end_of_work_compliance_review_hook
    ):
        result = invoke_end_of_work_compliance_review_hook(
            {
                "session_id": "abcdef12-rest-of-uuid",
                "transcript_path": "/tmp/should-never-be-read.jsonl",
                "stop_hook_active": True,
                "hook_event_name": "Stop",
            }
        )
        assert result.returncode == 0
        assert "decision" not in result.stdout
        assert "stop_hook_active=true" in result.stderr

    def test_does_not_invoke_transcript_parser_when_stop_hook_active(
        self, invoke_end_of_work_compliance_review_hook, tmp_path
    ):
        nonexistent_transcript_path = tmp_path / "transcript-that-does-not-exist.jsonl"
        result = invoke_end_of_work_compliance_review_hook(
            {
                "session_id": "abcdef12-rest-of-uuid",
                "transcript_path": str(nonexistent_transcript_path),
                "stop_hook_active": True,
                "hook_event_name": "Stop",
            }
        )
        assert result.returncode == 0
        assert "could not extract turn context" not in result.stderr
        assert "no transcript_path" not in result.stderr
