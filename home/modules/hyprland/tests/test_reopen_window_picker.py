import json
from unittest.mock import MagicMock, patch

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


class TestFormatEntryForDisplay:
    def test_formats_with_workspace_and_title(self):
        entry = {"workspace": 3, "title": "My Editor", "cmd": "code"}
        assert reopen_window_picker.format_entry_for_display(entry) == "[3] My Editor"

    def test_uses_defaults_for_missing_fields(self):
        entry = {"cmd": "kitty"}
        assert reopen_window_picker.format_entry_for_display(entry) == "[?] unknown"


class TestRunFuzzelPicker:
    def test_returns_selected_line(self):
        mock_result = MagicMock()
        mock_result.stdout = "[2] Browser\n"

        with patch(
            "reopen_window_picker.subprocess.run",
            return_value=mock_result,
        ) as mock_run:
            result = reopen_window_picker.run_fuzzel_picker(
                ["[1] Terminal", "[2] Browser"]
            )

            assert result == "[2] Browser"
            called_args = mock_run.call_args
            assert called_args[1]["input"] == "[2] Browser\n[1] Terminal"

    def test_returns_none_when_nothing_selected(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch(
            "reopen_window_picker.subprocess.run",
            return_value=mock_result,
        ):
            result = reopen_window_picker.run_fuzzel_picker(["[1] Terminal"])
            assert result is None

    def test_returns_none_when_output_is_whitespace(self):
        mock_result = MagicMock()
        mock_result.stdout = "   \n"

        with patch(
            "reopen_window_picker.subprocess.run",
            return_value=mock_result,
        ):
            result = reopen_window_picker.run_fuzzel_picker(["[1] Terminal"])
            assert result is None


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


class TestMainExitsWhenNoEntries:
    def test_exits_cleanly_when_no_history(self):
        with patch(
            "reopen_window_picker.load_history_entries",
            return_value=[],
        ):
            try:
                reopen_window_picker.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as exc:
                assert exc.code == 0


class TestMainExitsWhenNothingSelected:
    def test_exits_cleanly_when_picker_cancelled(self):
        entries = [{"cmd": "kitty", "workspace": 1, "title": "Terminal"}]

        with patch(
            "reopen_window_picker.load_history_entries",
            return_value=entries,
        ):
            with patch(
                "reopen_window_picker.run_fuzzel_picker",
                return_value=None,
            ):
                try:
                    reopen_window_picker.main()
                    assert False, "Should have raised SystemExit"
                except SystemExit as exc:
                    assert exc.code == 0


class TestMainReopensSelectedWindow:
    def test_reopens_matching_entry_and_removes_from_history(
        self, tmp_path, mock_subprocess_run
    ):
        history_file = tmp_path / "hypr-closed-windows-history"
        entries = [
            {"cmd": "kitty", "workspace": 1, "title": "Terminal"},
            {"cmd": "firefox", "workspace": 2, "title": "Browser"},
        ]
        history_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            with patch(
                "reopen_window_picker.load_history_entries",
                return_value=entries,
            ):
                with patch(
                    "reopen_window_picker.run_fuzzel_picker",
                    return_value="[1] Terminal",
                ):
                    reopen_window_picker.main()

        dispatched_args = mock_subprocess_run.call_args[0][0]
        dispatch_rule = " ".join(str(a) for a in dispatched_args)
        assert "kitty" in dispatch_rule

    def test_selects_last_match_when_duplicates_exist(
        self, tmp_path, mock_subprocess_run
    ):
        history_file = tmp_path / "hypr-closed-windows-history"
        entries = [
            {"cmd": "kitty --first", "workspace": 1, "title": "Terminal"},
            {"cmd": "kitty --second", "workspace": 1, "title": "Terminal"},
        ]
        history_file.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            with patch(
                "reopen_window_picker.load_history_entries",
                return_value=entries,
            ):
                with patch(
                    "reopen_window_picker.run_fuzzel_picker",
                    return_value="[1] Terminal",
                ):
                    reopen_window_picker.main()

        dispatched_args = mock_subprocess_run.call_args[0][0]
        dispatch_rule = " ".join(str(a) for a in dispatched_args)
        assert "kitty --second" in dispatch_rule


class TestMainExitsWhenSelectedEntryHasNoCommand:
    def test_exits_with_error_when_cmd_missing(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        entries = [{"workspace": 1, "title": "No cmd"}]
        history_file.write_text(json.dumps(entries[0]) + "\n")

        with patch.object(
            reopen_window_picker, "CLOSED_WINDOWS_HISTORY_FILE", history_file
        ):
            with patch(
                "reopen_window_picker.load_history_entries",
                return_value=entries,
            ):
                with patch(
                    "reopen_window_picker.run_fuzzel_picker",
                    return_value="[1] No cmd",
                ):
                    try:
                        reopen_window_picker.main()
                        assert False, "Should have raised SystemExit"
                    except SystemExit as exc:
                        assert exc.code == 1
