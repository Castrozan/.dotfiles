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


class TestStopPayloadLogging:
    def test_logs_payload_fields_on_every_invocation(
        self, invoke_end_of_work_compliance_review_hook
    ):
        result = invoke_end_of_work_compliance_review_hook(
            {
                "session_id": "abcdef12-rest-of-uuid",
                "transcript_path": "/tmp/example-transcript.jsonl",
                "cwd": "/Users/example/project",
                "stop_hook_active": False,
                "hook_event_name": "Stop",
            }
        )
        assert result.returncode == 0
        assert "received Stop payload" in result.stderr
        assert "hook_event_name=Stop" in result.stderr
        assert "stop_hook_active=False" in result.stderr
        assert "cwd=/Users/example/project" in result.stderr
        assert "transcript_path=/tmp/example-transcript.jsonl" in result.stderr

    def test_logs_payload_even_when_stop_hook_active_short_circuits(
        self, invoke_end_of_work_compliance_review_hook
    ):
        result = invoke_end_of_work_compliance_review_hook(
            {
                "session_id": "abcdef12-rest-of-uuid",
                "transcript_path": "/tmp/example.jsonl",
                "stop_hook_active": True,
                "hook_event_name": "Stop",
            }
        )
        assert result.returncode == 0
        assert "received Stop payload" in result.stderr
        assert "stop_hook_active=True" in result.stderr
        assert "stop_hook_active=true, allowing stop to avoid loop" in result.stderr
