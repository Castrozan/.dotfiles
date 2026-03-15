import json
from pathlib import Path
from unittest.mock import patch

import close_window_cycle as script


class TestReadProcessCmdline:
    def test_reads_null_separated_cmdline(self, tmp_path):
        cmdline_file = tmp_path / "cmdline"
        cmdline_file.write_bytes(b"/usr/bin/kitty\x00--config\x00foo.conf\x00")
        with patch.object(Path, "__new__", return_value=cmdline_file):
            pass
        raw_bytes = cmdline_file.read_bytes()
        result = raw_bytes.replace(b"\x00", b" ").decode().strip()
        assert result == "/usr/bin/kitty --config foo.conf"

    def test_returns_none_for_missing_process(self):
        result = script.read_process_cmdline(999999999)
        assert result is None


class TestSaveWindowToHistory:
    def test_appends_json_entry_to_history_file(self, tmp_path):
        history_file = tmp_path / "history"
        with patch.object(script, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            script.save_window_to_history(0, "", 1, "test")
            assert not history_file.exists()

    def test_skips_when_no_launch_command(self, tmp_path):
        history_file = tmp_path / "history"
        with patch.object(script, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            script.save_window_to_history(0, "kitty", 1, "Terminal")
            assert not history_file.exists()


class TestTruncateHistoryFile:
    def test_keeps_only_max_entries(self, tmp_path):
        history_file = tmp_path / "history"
        entries = [
            json.dumps(
                {"cmd": f"cmd{i}", "class": "test", "workspace": 1, "title": f"t{i}"}
            )
            for i in range(15)
        ]
        history_file.write_text("\n".join(entries) + "\n")
        with patch.object(script, "CLOSED_WINDOWS_HISTORY_FILE", history_file):
            with patch.object(script, "MAX_HISTORY_ENTRIES", 10):
                script.truncate_history_file_to_max_entries()
        lines = history_file.read_text().splitlines()
        assert len(lines) == 10
        assert '"cmd14"' in lines[-1]


class TestFindPreviousWindowOnWorkspace:
    def test_finds_window_with_lowest_focus_history_id(
        self, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("clients", sample_hyprland_clients)
        result = script.find_previous_window_on_workspace(1, "0xbbb")
        assert result == "0xaaa"

    def test_returns_none_when_no_other_windows(self, hyprctl_response_builder):
        hyprctl_response_builder(
            "clients",
            [{"address": "0xonly", "workspace": {"id": 1}, "focusHistoryID": 0}],
        )
        result = script.find_previous_window_on_workspace(1, "0xonly")
        assert result is None


class TestMainEnsuresWorkspaceGroupedAfterClose:
    @patch("close_window_cycle.time.sleep")
    def test_regroups_remaining_windows_after_closing_grouped_window(
        self, mock_sleep, mock_subprocess_run, hyprctl_response_builder
    ):
        three_grouped_tiled_clients = [
            {
                "address": "0xaaa",
                "workspace": {"id": 1},
                "class": "kitty",
                "title": "Terminal",
                "pid": 1234,
                "floating": False,
                "focusHistoryID": 0,
                "grouped": ["0xaaa", "0xbbb", "0xccc"],
            },
            {
                "address": "0xbbb",
                "workspace": {"id": 1},
                "class": "firefox",
                "title": "Browser",
                "pid": 5678,
                "floating": False,
                "focusHistoryID": 1,
                "grouped": ["0xaaa", "0xbbb", "0xccc"],
            },
            {
                "address": "0xccc",
                "workspace": {"id": 1},
                "class": "code",
                "title": "Editor",
                "pid": 9012,
                "floating": False,
                "focusHistoryID": 2,
                "grouped": ["0xaaa", "0xbbb", "0xccc"],
            },
        ]
        hyprctl_response_builder("activewindow", three_grouped_tiled_clients[1])
        hyprctl_response_builder("clients", three_grouped_tiled_clients)

        with patch.object(
            script,
            "ensure_remaining_tiled_windows_are_grouped_on_active_workspace",
        ) as mock_ensure_grouped:
            script.main()
            mock_ensure_grouped.assert_called_once()
