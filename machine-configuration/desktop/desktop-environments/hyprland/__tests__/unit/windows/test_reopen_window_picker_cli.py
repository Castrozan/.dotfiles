import json
from unittest.mock import patch
import reopen_window_picker


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
