import json
from pathlib import Path

import pytest

import end_of_work_compliance_review as hook


@pytest.fixture(autouse=True)
def _apply_compliance_review_test_isolation(
    reset_session_id_prefix_between_tests, isolate_persistent_log_file
):
    return isolate_persistent_log_file


def _write_transcript(tmp_path: Path, entries: list[dict]) -> Path:
    transcript_path = tmp_path / "session.jsonl"
    with open(transcript_path, "w") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")
    return transcript_path


class TestSessionStartTimestampExtraction:
    def test_picks_first_entry_with_a_timestamp(self, tmp_path):
        transcript_path = _write_transcript(
            tmp_path,
            [
                {"type": "summary"},
                {
                    "type": "user",
                    "message": {"role": "user", "content": "real prompt"},
                    "timestamp": "2026-05-19T15:00:00.000Z",
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "tool_use", "name": "Edit", "input": {}}],
                    },
                    "timestamp": "2026-05-19T15:00:05.000Z",
                },
            ],
        )

        context = hook.extract_current_turn_context_from_transcript(transcript_path)
        assert context["session_start_timestamp"] == "2026-05-19T15:00:00.000Z"


class TestToolResultCollection:
    def test_collects_tool_results_keyed_by_use_id(self, tmp_path):
        transcript_path = _write_transcript(
            tmp_path,
            [
                {
                    "type": "user",
                    "message": {"role": "user", "content": "do the thing"},
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "call_abc",
                                "name": "Bash",
                                "input": {"command": "ls"},
                            },
                        ],
                    },
                },
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": "call_abc",
                                "content": "foo.txt\nbar.txt",
                            }
                        ],
                    },
                },
            ],
        )

        context = hook.extract_current_turn_context_from_transcript(transcript_path)
        assert context["tool_results_by_use_id"] == {"call_abc": "foo.txt\nbar.txt"}

    def test_flattens_list_content_in_tool_results(self, tmp_path):
        transcript_path = _write_transcript(
            tmp_path,
            [
                {
                    "type": "user",
                    "message": {"role": "user", "content": "do the thing"},
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "call_xyz",
                                "name": "Read",
                                "input": {"file_path": "/x"},
                            },
                        ],
                    },
                },
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": "call_xyz",
                                "content": [
                                    {"type": "text", "text": "first chunk"},
                                    {"type": "text", "text": "second chunk"},
                                ],
                            }
                        ],
                    },
                },
            ],
        )

        context = hook.extract_current_turn_context_from_transcript(transcript_path)
        assert (
            context["tool_results_by_use_id"]["call_xyz"] == "first chunk\nsecond chunk"
        )


class TestPriorAssistantMessageCollection:
    def test_collects_text_from_earlier_assistant_replies(self, tmp_path):
        transcript_path = _write_transcript(
            tmp_path,
            [
                {
                    "type": "user",
                    "message": {"role": "user", "content": "first ask"},
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "text", "text": "first reply"}],
                    },
                },
                {
                    "type": "user",
                    "message": {"role": "user", "content": "current ask"},
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [{"type": "tool_use", "name": "Edit", "input": {}}],
                    },
                },
            ],
        )

        context = hook.extract_current_turn_context_from_transcript(transcript_path)
        assert context["prior_assistant_messages"] == ["first reply"]
