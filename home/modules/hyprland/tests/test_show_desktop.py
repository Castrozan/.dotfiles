from unittest.mock import patch

import show_desktop as script


class TestHideAllWorkspaceWindowsToSpecialDesktop:
    def test_saves_window_addresses_to_state_file(
        self, tmp_path, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("activewindow", {"address": "0xaaa"})
        hyprctl_response_builder("clients", sample_hyprland_clients)
        with patch.object(script, "STATE_DIR", tmp_path):
            script.hide_all_workspace_windows_to_special_desktop(1)
        state_file = tmp_path / "ws-1"
        assert state_file.exists()
        addresses = state_file.read_text().splitlines()
        assert "0xaaa" in addresses
        assert "0xbbb" in addresses
        assert "0xddd" in addresses

    def test_saves_focused_window_address(
        self, tmp_path, hyprctl_response_builder, sample_hyprland_clients
    ):
        hyprctl_response_builder("activewindow", {"address": "0xaaa"})
        hyprctl_response_builder("clients", sample_hyprland_clients)
        with patch.object(script, "STATE_DIR", tmp_path):
            script.hide_all_workspace_windows_to_special_desktop(1)
        focus_file = tmp_path / "focus-1"
        assert focus_file.read_text() == "0xaaa"

    def test_does_nothing_when_no_windows(self, tmp_path, hyprctl_response_builder):
        hyprctl_response_builder("activewindow", {"address": "0xaaa"})
        hyprctl_response_builder("clients", [])
        with patch.object(script, "STATE_DIR", tmp_path):
            script.hide_all_workspace_windows_to_special_desktop(1)
        assert not (tmp_path / "ws-1").exists()


class TestRestoreHiddenWindowsAndMaximize:
    @patch("show_desktop.subprocess.run")
    @patch("show_desktop.time.sleep")
    def test_restores_windows_from_state_file(
        self, mock_sleep, mock_subproc, tmp_path, mock_subprocess_run
    ):
        state_file = tmp_path / "ws-1"
        state_file.write_text("0xaaa\n0xbbb\n")
        with patch.object(script, "STATE_DIR", tmp_path):
            script.restore_hidden_windows_and_maximize(1)
        assert not state_file.exists()

    @patch("show_desktop.subprocess.run")
    @patch("show_desktop.time.sleep")
    def test_restores_focus_to_saved_window(
        self, mock_sleep, mock_subproc, tmp_path, mock_subprocess_run
    ):
        state_file = tmp_path / "ws-1"
        state_file.write_text("0xaaa\n")
        focus_file = tmp_path / "focus-1"
        focus_file.write_text("0xaaa")
        with patch.object(script, "STATE_DIR", tmp_path):
            script.restore_hidden_windows_and_maximize(1)
        assert not focus_file.exists()
