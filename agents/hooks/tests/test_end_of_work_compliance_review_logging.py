import io
from unittest.mock import patch

import pytest

import end_of_work_compliance_review as hook


@pytest.fixture(autouse=True)
def _apply_compliance_review_test_isolation(
    reset_session_id_prefix_between_tests, isolate_persistent_log_file
):
    return isolate_persistent_log_file


class TestLogStatus:
    def test_writes_timestamp_and_prefix_to_stderr(self):
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            hook.log_status("test message")
            output = mock_stderr.getvalue()
            assert "end-of-work-compliance-review: test message" in output
            assert output.startswith("[")

    def test_includes_session_id_short_prefix_when_set(self):
        hook.set_session_id_short_prefix("abcdef12-rest-of-uuid")
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            with patch("time.strftime", return_value="2026-05-18 10:30:45"):
                hook.log_status("test message")
                assert mock_stderr.getvalue() == (
                    "[2026-05-18 10:30:45] [abcdef12] "
                    "end-of-work-compliance-review: test message\n"
                )

    def test_omits_session_segment_when_session_id_blank(self):
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            with patch("time.strftime", return_value="2026-05-18 10:30:45"):
                hook.log_status("test message")
                assert mock_stderr.getvalue() == (
                    "[2026-05-18 10:30:45] "
                    "end-of-work-compliance-review: test message\n"
                )

    def test_appends_to_persistent_log_file(self, isolate_persistent_log_file):
        hook.log_status("line one")
        hook.log_status("line two")
        log_contents = isolate_persistent_log_file.read_text()
        assert "line one" in log_contents
        assert "line two" in log_contents


class TestSetSessionIdShortPrefix:
    def test_truncates_to_first_eight_characters(self):
        hook.set_session_id_short_prefix("773a6460-33b0-4510-802a-d73a4921b4fe")
        assert hook.get_session_id_short_prefix() == "773a6460"

    def test_handles_empty_session_id(self):
        hook.set_session_id_short_prefix("")
        assert hook.get_session_id_short_prefix() == ""
