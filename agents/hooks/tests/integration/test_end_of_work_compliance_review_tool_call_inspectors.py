import json
from pathlib import Path

import pytest

import end_of_work_compliance_review as hook
from end_of_work_compliance_review_tool_call_inspectors import (
    find_parking_tool_calls,
    has_any_file_mutating_tool_call,
)

END_OF_WORK_COMPLIANCE_REVIEW_HOOK_SCRIPT_PATH = next(
    Path(__file__).resolve().parent.parent.parent.rglob("end-of-work-compliance-review.py")
)


@pytest.fixture(autouse=True)
def _apply_compliance_review_test_isolation(
    reset_session_id_prefix_between_tests, isolate_persistent_log_file
):
    return isolate_persistent_log_file


class TestHasAnyFileMutatingToolCall:
    def test_returns_true_when_edit_present(self):
        assert has_any_file_mutating_tool_call([{"name": "Read"}, {"name": "Edit"}])

    def test_returns_true_for_write_notebookedit_update(self):
        assert has_any_file_mutating_tool_call([{"name": "Write"}])
        assert has_any_file_mutating_tool_call([{"name": "NotebookEdit"}])
        assert has_any_file_mutating_tool_call([{"name": "Update"}])

    def test_returns_false_for_read_only_tools(self):
        assert not has_any_file_mutating_tool_call(
            [{"name": "Read"}, {"name": "Bash"}, {"name": "Grep"}]
        )

    def test_returns_false_for_empty_list(self):
        assert not has_any_file_mutating_tool_call([])


class TestFindParkingToolCalls:
    def test_returns_empty_when_only_synchronous_tools(self):
        tool_calls = [
            {"id": "toolu_a", "name": "Edit"},
            {"id": "toolu_b", "name": "Read"},
            {"id": "toolu_c", "name": "Bash", "input": {"command": "ls"}},
        ]
        assert find_parking_tool_calls(tool_calls) == []

    def test_returns_monitor_calls(self):
        tool_calls = [
            {"id": "toolu_a", "name": "Edit"},
            {"id": "toolu_b", "name": "Monitor", "input": {"command": "tail -f"}},
        ]
        parking = find_parking_tool_calls(tool_calls)
        assert len(parking) == 1
        assert parking[0]["name"] == "Monitor"

    def test_returns_schedule_wakeup_calls(self):
        tool_calls = [{"id": "toolu_a", "name": "ScheduleWakeup", "input": {}}]
        assert find_parking_tool_calls(tool_calls) == tool_calls

    def test_returns_backgrounded_bash_calls(self):
        tool_calls = [
            {
                "id": "toolu_a",
                "name": "Bash",
                "input": {"command": "long-running", "run_in_background": True},
            }
        ]
        assert find_parking_tool_calls(tool_calls) == tool_calls

    def test_skips_foreground_bash_calls(self):
        tool_calls = [
            {
                "id": "toolu_a",
                "name": "Bash",
                "input": {"command": "ls", "run_in_background": False},
            }
        ]
        assert find_parking_tool_calls(tool_calls) == []


class TestEndToEndParkedTurnSkip:
    def _write_transcript(self, tmp_path: Path, entries: list[dict]) -> Path:
        transcript_path = tmp_path / "session.jsonl"
        with open(transcript_path, "w") as handle:
            for entry in entries:
                handle.write(json.dumps(entry) + "\n")
        return transcript_path

    def test_skips_review_when_monitor_tool_call_has_no_result(
        self, tmp_path, capsys, monkeypatch
    ):
        transcript_path = self._write_transcript(
            tmp_path,
            [
                {
                    "type": "user",
                    "message": {"role": "user", "content": "kick off the rebuild"},
                    "cwd": str(tmp_path),
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "toolu_edit_done",
                                "name": "Edit",
                                "input": {"file_path": "foo.py"},
                            },
                            {
                                "type": "tool_use",
                                "id": "toolu_monitor_pending",
                                "name": "Monitor",
                                "input": {"command": "tail -f log"},
                            },
                        ],
                    },
                    "cwd": str(tmp_path),
                },
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": "toolu_edit_done",
                                "content": "ok",
                            }
                        ],
                    },
                },
            ],
        )

        monkeypatch.setattr(
            "sys.stdin",
            __import__("io").StringIO(
                json.dumps(
                    {
                        "session_id": "abcdef12-rest-of-uuid",
                        "transcript_path": str(transcript_path),
                        "stop_hook_active": False,
                        "hook_event_name": "Stop",
                    }
                )
            ),
        )

        with pytest.raises(SystemExit) as exit_info:
            hook.main()

        assert exit_info.value.code == 0
        captured = capsys.readouterr()
        assert "decision" not in captured.out
        assert "agent parked on 1 yielding tool call(s) (Monitor)" in captured.err
