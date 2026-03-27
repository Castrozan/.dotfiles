from unittest.mock import patch

import session_context


def make_hyprland_client(workspace_id, window_class, window_title="", address="0xaaa"):
    return {
        "address": address,
        "workspace": {"id": workspace_id},
        "class": window_class,
        "title": window_title,
        "pid": 1234,
        "floating": False,
    }


class TestExtractVscodeProjectNameFromTitle:
    def test_standard_vscode_title_with_file_and_project(self):
        title = "flake.nix - dotfiles - Visual Studio Code"
        assert (
            session_context.extract_vscode_project_name_from_title(title) == "dotfiles"
        )

    def test_vscode_title_with_only_project(self):
        title = "oauth - Visual Studio Code"
        assert session_context.extract_vscode_project_name_from_title(title) == "oauth"

    def test_vscode_title_with_nested_dashes_in_filename(self):
        title = "my-config-file.yaml - my-project - Visual Studio Code"
        assert (
            session_context.extract_vscode_project_name_from_title(title)
            == "my-project"
        )

    def test_non_vscode_title_truncated(self):
        title = "Some Random Window Title"
        result = session_context.extract_vscode_project_name_from_title(title)
        assert result == "Some Random Window Title"

    def test_long_non_vscode_title_truncated_at_40_chars(self):
        title = "A" * 60
        result = session_context.extract_vscode_project_name_from_title(title)
        assert len(result) == 40


class TestSummarizeWorkspaceWindows:
    def test_empty_client_list(self):
        assert session_context.summarize_workspace_windows([], 1) == []

    def test_single_vscode_window(self):
        clients = [
            make_hyprland_client(1, "code", "flake.nix - dotfiles - Visual Studio Code")
        ]
        result = session_context.summarize_workspace_windows(clients, 1)
        assert result == ["code: dotfiles"]

    def test_single_terminal(self):
        clients = [make_hyprland_client(1, "org.wezfurlong.wezterm", "fish")]
        result = session_context.summarize_workspace_windows(clients, 1)
        assert result == ["wezterm"]

    def test_multiple_terminals_counted(self):
        clients = [
            make_hyprland_client(1, "org.wezfurlong.wezterm", "fish", address="0xaaa"),
            make_hyprland_client(1, "org.wezfurlong.wezterm", "nvim", address="0xbbb"),
        ]
        result = session_context.summarize_workspace_windows(clients, 1)
        assert result == ["wezterm (x2)"]

    def test_browser_shows_short_class_and_title(self):
        clients = [make_hyprland_client(1, "brave-browser", "YouTube Music - Brave")]
        result = session_context.summarize_workspace_windows(clients, 1)
        assert result == ["brave: YouTube Music - Brave"]

    def test_chrome_global_browser(self):
        clients = [make_hyprland_client(1, "chrome-global", "Google Docs - Chrome")]
        result = session_context.summarize_workspace_windows(clients, 1)
        assert result == ["chrome: Google Docs - Chrome"]

    def test_filters_to_correct_workspace(self):
        clients = [
            make_hyprland_client(
                1, "code", "a.py - proj-a - Visual Studio Code", address="0x1"
            ),
            make_hyprland_client(
                2, "code", "b.py - proj-b - Visual Studio Code", address="0x2"
            ),
        ]
        result = session_context.summarize_workspace_windows(clients, 2)
        assert result == ["code: proj-b"]

    def test_unknown_class_shown_as_is(self):
        clients = [make_hyprland_client(1, "pavucontrol", "Volume Control")]
        result = session_context.summarize_workspace_windows(clients, 1)
        assert result == ["pavucontrol"]

    def test_mixed_workspace_with_vscode_browser_and_terminals(self):
        clients = [
            make_hyprland_client(
                10, "code", "index.ts - oauth - Visual Studio Code", address="0x1"
            ),
            make_hyprland_client(
                10, "brave-browser", "YouTube Music - Brave", address="0x2"
            ),
            make_hyprland_client(10, "org.wezfurlong.wezterm", "fish", address="0x3"),
        ]
        result = session_context.summarize_workspace_windows(clients, 10)
        assert "code: oauth" in result
        assert "brave: YouTube Music - Brave" in result
        assert "wezterm" in result

    def test_kitty_terminal_counted(self):
        clients = [make_hyprland_client(1, "kitty", "bash")]
        result = session_context.summarize_workspace_windows(clients, 1)
        assert result == ["wezterm"]


class TestDetectHyprlandWorkspaceContext:
    @patch("session_context.run_command_with_timeout")
    def test_returns_empty_when_hyprctl_unavailable(self, mock_run):
        mock_run.return_value = (1, "")
        assert session_context.detect_hyprland_workspace_context() == {}

    @patch("session_context.run_command_with_timeout")
    def test_returns_workspace_id_and_monitor(self, mock_run):
        import json

        workspace_response = json.dumps(
            {"id": 25, "name": "25", "monitor": "DP-2", "windows": 3}
        )
        clients_response = json.dumps([])

        mock_run.side_effect = [
            (0, workspace_response),
            (0, clients_response),
        ]

        result = session_context.detect_hyprland_workspace_context()
        assert result["id"] == 25
        assert result["monitor"] == "DP-2"

    @patch("session_context.run_command_with_timeout")
    def test_returns_context_without_windows_when_clients_fail(self, mock_run):
        import json

        workspace_response = json.dumps({"id": 10, "monitor": "HDMI-A-1"})
        mock_run.side_effect = [
            (0, workspace_response),
            (1, ""),
        ]

        result = session_context.detect_hyprland_workspace_context()
        assert result["id"] == 10
        assert "windows" not in result

    @patch("session_context.run_command_with_timeout")
    def test_includes_window_summaries(self, mock_run):
        import json

        workspace_response = json.dumps({"id": 10, "monitor": "DP-1"})
        clients_response = json.dumps(
            [
                make_hyprland_client(
                    10, "code", "main.py - oauth - Visual Studio Code"
                ),
                make_hyprland_client(10, "org.wezfurlong.wezterm", "fish"),
            ]
        )

        mock_run.side_effect = [
            (0, workspace_response),
            (0, clients_response),
        ]

        result = session_context.detect_hyprland_workspace_context()
        assert "code: oauth" in result["windows"]
        assert "wezterm" in result["windows"]


class TestFormatHyprlandWorkspaceSection:
    def test_workspace_with_monitor_and_windows(self):
        context = {
            "id": 25,
            "monitor": "DP-2",
            "windows": ["code: dotfiles", "wezterm (x2)"],
        }
        result = session_context.format_hyprland_workspace_section(context)
        assert result == "Workspace: #25 on DP-2 | code: dotfiles, wezterm (x2)"

    def test_workspace_without_monitor(self):
        context = {"id": 1, "monitor": "", "windows": ["code: project"]}
        result = session_context.format_hyprland_workspace_section(context)
        assert result == "Workspace: #1 | code: project"

    def test_workspace_without_windows(self):
        context = {"id": 5, "monitor": "DP-1"}
        result = session_context.format_hyprland_workspace_section(context)
        assert result == "Workspace: #5 on DP-1"
