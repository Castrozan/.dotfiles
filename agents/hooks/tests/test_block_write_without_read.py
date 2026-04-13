import json
from unittest.mock import patch

import block_write_without_read


class TestExtractTargetFilePathFromToolInput:
    def test_returns_file_path_when_present(self):
        payload = {"tool_input": {"file_path": "/abs/path.py"}}
        assert (
            block_write_without_read.extract_target_file_path_from_tool_input(payload)
            == "/abs/path.py"
        )

    def test_returns_none_when_tool_input_missing(self):
        assert (
            block_write_without_read.extract_target_file_path_from_tool_input({})
            is None
        )

    def test_returns_none_when_file_path_missing(self):
        payload = {"tool_input": {"content": "x"}}
        assert (
            block_write_without_read.extract_target_file_path_from_tool_input(payload)
            is None
        )


class TestWasTargetFileReadInThisSession:
    def test_detects_read_tool_call_with_matching_path(self):
        transcript_lines = [
            json.dumps(
                {
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Read",
                                "input": {"file_path": "/target.py"},
                            }
                        ]
                    }
                }
            ),
        ]
        assert block_write_without_read.was_target_file_read_in_this_session(
            "/target.py", transcript_lines
        )

    def test_ignores_read_for_different_path(self):
        transcript_lines = [
            json.dumps(
                {
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Read",
                                "input": {"file_path": "/other.py"},
                            }
                        ]
                    }
                }
            ),
        ]
        assert not block_write_without_read.was_target_file_read_in_this_session(
            "/target.py", transcript_lines
        )

    def test_ignores_grep_even_on_same_path(self):
        transcript_lines = [
            json.dumps(
                {
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Grep",
                                "input": {"path": "/target.py"},
                            }
                        ]
                    }
                }
            ),
        ]
        assert not block_write_without_read.was_target_file_read_in_this_session(
            "/target.py", transcript_lines
        )

    def test_handles_malformed_transcript_lines(self):
        transcript_lines = ["not-json", "{broken", ""]
        assert not block_write_without_read.was_target_file_read_in_this_session(
            "/x.py", transcript_lines
        )

    def test_empty_transcript_returns_false(self):
        assert not block_write_without_read.was_target_file_read_in_this_session(
            "/x.py", []
        )


class TestTargetFileAlreadyExistsOnDisk:
    def test_returns_true_when_file_exists(self, tmp_path):
        p = tmp_path / "exists.txt"
        p.write_text("hello")
        assert block_write_without_read.target_file_already_exists_on_disk(str(p))

    def test_returns_false_when_file_does_not_exist(self, tmp_path):
        missing = tmp_path / "missing.txt"
        assert not block_write_without_read.target_file_already_exists_on_disk(
            str(missing)
        )

    def test_returns_false_when_path_is_directory(self, tmp_path):
        assert not block_write_without_read.target_file_already_exists_on_disk(
            str(tmp_path)
        )


class TestDenyWithReminder:
    def test_returns_pretooluse_deny_payload(self):
        result = block_write_without_read.deny_with_reminder("/target.py")
        assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "/target.py" in result["hookSpecificOutput"]["permissionDecisionReason"]
        assert "Read" in result["hookSpecificOutput"]["permissionDecisionReason"]
