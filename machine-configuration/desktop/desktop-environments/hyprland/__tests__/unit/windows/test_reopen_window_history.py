import json
from unittest.mock import patch
import reopen_window_picker


class TestLoadHistoryEntries:
    def test_returns_empty_list_when_file_missing(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            assert reopen_window_picker.load_history_entries() == []

    def test_returns_empty_list_when_file_empty(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        history_file.write_text("")

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            assert reopen_window_picker.load_history_entries() == []

    def test_parses_json_lines_into_list(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        entries = [
            {"cmd": "kitty", "workspace": 1, "title": "Terminal"},
            {"cmd": "firefox", "workspace": 2, "title": "Browser"},
        ]
        history_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            result = reopen_window_picker.load_history_entries()

        assert len(result) == 2
        assert result[0]["cmd"] == "kitty"
        assert result[1]["cmd"] == "firefox"

    def test_skips_blank_lines(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        history_file.write_text(
            json.dumps({"cmd": "kitty", "workspace": 1, "title": "T"})
            + "\n\n"
            + json.dumps({"cmd": "code", "workspace": 2, "title": "E"})
            + "\n"
        )

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            result = reopen_window_picker.load_history_entries()

        assert len(result) == 2


class TestRemoveEntryFromHistoryByLineNumber:
    def test_removes_first_line(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        history_file.write_text("line0\nline1\nline2\n")

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            reopen_window_picker.remove_entry_from_history_by_line_number(0)

        assert "line0" not in history_file.read_text()
        assert "line1" in history_file.read_text()
        assert "line2" in history_file.read_text()

    def test_removes_last_line(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        history_file.write_text("line0\nline1\n")

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            reopen_window_picker.remove_entry_from_history_by_line_number(1)

        content = history_file.read_text()
        assert "line0" in content
        assert "line1" not in content

    def test_empties_file_when_removing_only_line(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        history_file.write_text("only-line\n")

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            reopen_window_picker.remove_entry_from_history_by_line_number(0)

        assert history_file.read_text() == ""
