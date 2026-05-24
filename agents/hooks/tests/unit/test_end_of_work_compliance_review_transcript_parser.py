import json
from pathlib import Path

import pytest

import end_of_work_compliance_review as hook


@pytest.fixture(autouse=True)
def _apply_compliance_review_test_isolation(
    reset_session_id_prefix_between_tests, isolate_persistent_log_file
):
    return isolate_persistent_log_file


class TestExtractCurrentTurnContextFromTranscript:
    def _write_transcript(self, tmp_path: Path, entries: list[dict]) -> Path:
        transcript_path = tmp_path / "session.jsonl"
        with open(transcript_path, "w") as handle:
            for entry in entries:
                handle.write(json.dumps(entry) + "\n")
        return transcript_path

    def test_returns_empty_when_transcript_missing(self, tmp_path):
        missing_path = tmp_path / "no-such-file.jsonl"
        assert hook.extract_current_turn_context_from_transcript(missing_path) == {}

    def test_extracts_last_user_prompt_and_subsequent_tool_calls(self, tmp_path):
        transcript_path = self._write_transcript(
            tmp_path,
            [
                {
                    "type": "user",
                    "message": {"role": "user", "content": "old request"},
                    "cwd": "/repo",
                },
                {
                    "type": "user",
                    "message": {"role": "user", "content": "fix the bug in foo.py"},
                    "cwd": "/repo",
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Read",
                                "input": {"file_path": "foo.py"},
                            },
                            {
                                "type": "tool_use",
                                "name": "Edit",
                                "input": {"file_path": "foo.py"},
                            },
                            {"type": "text", "text": "Fixed it"},
                        ],
                    },
                    "cwd": "/repo",
                },
            ],
        )

        context = hook.extract_current_turn_context_from_transcript(transcript_path)

        assert context["current_user_prompts"] == ["fix the bug in foo.py"]
        assert context["prior_user_prompts"] == ["old request"]
        assert [call["name"] for call in context["ordered_tool_calls"]] == [
            "Read",
            "Edit",
        ]
        assert context["assistant_text"] == "Fixed it"
        assert context["workspace_cwd"] == "/repo"

    def test_ignores_sidechain_entries(self, tmp_path):
        transcript_path = self._write_transcript(
            tmp_path,
            [
                {
                    "type": "user",
                    "message": {"role": "user", "content": "main request"},
                },
                {
                    "type": "user",
                    "isSidechain": True,
                    "message": {"role": "user", "content": "subagent task"},
                },
                {
                    "type": "assistant",
                    "isSidechain": True,
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "tool_use", "name": "Read", "input": {}},
                        ],
                    },
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "tool_use", "name": "Edit", "input": {}},
                        ],
                    },
                },
            ],
        )

        context = hook.extract_current_turn_context_from_transcript(transcript_path)

        assert context["current_user_prompts"] == ["main request"]
        assert [call["name"] for call in context["ordered_tool_calls"]] == ["Edit"]

    def test_skips_tool_result_user_entries_when_finding_boundary(self, tmp_path):
        transcript_path = self._write_transcript(
            tmp_path,
            [
                {
                    "type": "user",
                    "message": {"role": "user", "content": "real prompt"},
                },
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "tool_use", "name": "Read", "input": {}},
                        ],
                    },
                },
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [
                            {"type": "tool_result", "content": "file contents here"},
                        ],
                    },
                },
            ],
        )

        context = hook.extract_current_turn_context_from_transcript(transcript_path)
        assert context["current_user_prompts"] == ["real prompt"]
