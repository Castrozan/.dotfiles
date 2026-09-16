import json
from unittest.mock import patch

import reopen_window


class TestMainExitsWhenNoHistoryFile:
    def test_exits_cleanly_when_history_file_missing(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"

        with patch.object(reopen_window, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            try:
                reopen_window.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as exc:
                assert exc.code == 0


class TestMainExitsWhenHistoryFileEmpty:
    def test_exits_cleanly_when_history_file_has_no_lines(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        history_file.write_text("")

        with patch.object(reopen_window, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            try:
                reopen_window.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as exc:
                assert exc.code == 0


class TestMainReopensLastClosedWindow:
    def test_dispatches_last_entry_and_removes_it_from_history(
        self, tmp_path, mock_subprocess_run
    ):
        history_file = tmp_path / "hypr-closed-windows-history"
        entries = [
            json.dumps({"cmd": "kitty", "workspace": 1, "title": "Terminal"}),
            json.dumps({"cmd": "firefox", "workspace": 2, "title": "Browser"}),
        ]
        history_file.write_text("\n".join(entries) + "\n")

        with patch.object(reopen_window, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            reopen_window.main()

        remaining = history_file.read_text().strip()
        assert "kitty" in remaining
        assert "firefox" not in remaining

        dispatched_args = mock_subprocess_run.call_args[0][0]
        assert "hyprctl" in dispatched_args
        assert any("firefox" in str(arg) for arg in dispatched_args)

    def test_clears_history_when_only_one_entry(self, tmp_path, mock_subprocess_run):
        history_file = tmp_path / "hypr-closed-windows-history"
        entry = json.dumps({"cmd": "code", "workspace": 3, "title": "Editor"})
        history_file.write_text(entry + "\n")

        with patch.object(reopen_window, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            reopen_window.main()

        assert history_file.read_text() == ""


class TestMainExitsWhenLaunchCommandMissing:
    def test_exits_with_error_when_cmd_field_empty(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        entry = json.dumps({"cmd": "", "workspace": 1, "title": "Bad"})
        history_file.write_text(entry + "\n")

        with patch.object(reopen_window, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            try:
                reopen_window.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as exc:
                assert exc.code == 1

    def test_exits_with_error_when_cmd_field_absent(self, tmp_path):
        history_file = tmp_path / "hypr-closed-windows-history"
        entry = json.dumps({"workspace": 1, "title": "No cmd"})
        history_file.write_text(entry + "\n")

        with patch.object(reopen_window, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            try:
                reopen_window.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as exc:
                assert exc.code == 1


class TestMainDispatchesWithCorrectWorkspace:
    def test_uses_workspace_from_history_entry(self, tmp_path, mock_subprocess_run):
        history_file = tmp_path / "hypr-closed-windows-history"
        entry = json.dumps({"cmd": "alacritty", "workspace": 7, "title": "Term"})
        history_file.write_text(entry + "\n")

        with patch.object(reopen_window, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            reopen_window.main()

        dispatched_args = mock_subprocess_run.call_args[0][0]
        dispatch_rule = " ".join(str(a) for a in dispatched_args)
        assert "workspace 7 silent" in dispatch_rule
        assert "alacritty" in dispatch_rule
