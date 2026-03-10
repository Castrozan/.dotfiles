from unittest.mock import MagicMock, call, patch

import menu


class TestShowFuzzelMenu:
    def test_builds_basic_command_with_prompt(self):
        mock_result = MagicMock()
        mock_result.stdout = "selected option\n"

        with patch("menu.subprocess.run", return_value=mock_result) as mock_run:
            result = menu.show_fuzzel_menu("Test", "option1\noption2")

            assert result == "selected option"
            mock_run.assert_called_once_with(
                [
                    "hypr-fuzzel",
                    "--dmenu",
                    "--width",
                    "30",
                    "--lines",
                    "10",
                    "--prompt",
                    "Test> ",
                ],
                input="option1\noption2",
                capture_output=True,
                text=True,
            )

    def test_appends_extra_args_when_provided(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("menu.subprocess.run", return_value=mock_result) as mock_run:
            menu.show_fuzzel_menu("Test", "opts", "--width 350")

            args = mock_run.call_args[0][0]
            assert "--width" in args
            assert "350" in args

    def test_adds_preselect_index_when_matching(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("menu.subprocess.run", return_value=mock_result) as mock_run:
            menu.show_fuzzel_menu("Test", "alpha\nbeta\ngamma", preselect="beta")

            args = mock_run.call_args[0][0]
            assert "-c" in args
            assert "2" in args

    def test_no_preselect_index_when_not_matching(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("menu.subprocess.run", return_value=mock_result) as mock_run:
            menu.show_fuzzel_menu("Test", "alpha\nbeta", preselect="missing")

            args = mock_run.call_args[0][0]
            assert "-c" not in args

    def test_returns_empty_string_when_cancelled(self):
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("menu.subprocess.run", return_value=mock_result):
            assert menu.show_fuzzel_menu("Test", "opts") == ""


class TestShowThemeMenu:
    def test_sets_theme_when_selected(self):
        def run_side_effect(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if "hypr-theme-list" in args:
                result.stdout = "tokyonight\ncatppuccin\n"
            elif "hypr-theme-current" in args:
                result.stdout = "tokyonight\n"
            elif "hypr-fuzzel" in args[0]:
                result.stdout = "catppuccin\n"
            return result

        with patch("menu.subprocess.run", side_effect=run_side_effect) as mock_run:
            menu.show_theme_menu(back_to_exit=True)

            assert call(["hypr-theme-set", "catppuccin"]) in mock_run.call_args_list

    def test_exits_when_cancelled_and_back_to_exit(self):
        def run_side_effect(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            if "hypr-theme-list" in args:
                result.stdout = "tokyonight\n"
            elif "hypr-theme-current" in args:
                result.stdout = "tokyonight\n"
            return result

        with patch("menu.subprocess.run", side_effect=run_side_effect) as mock_run:
            menu.show_theme_menu(back_to_exit=True)

            for c in mock_run.call_args_list:
                assert "hypr-theme-set" not in c[0][0]


class TestShowSystemMenu:
    def test_locks_screen_when_lock_selected(self):
        with patch("menu.show_fuzzel_menu", return_value="  Lock"):
            with patch("menu.subprocess.run") as mock_run:
                menu.show_system_menu(back_to_exit=True)

                mock_run.assert_called_once_with(["hyprlock"])

    def test_reboots_when_restart_selected(self):
        with patch("menu.show_fuzzel_menu", return_value="󰜉  Restart"):
            with patch("menu.subprocess.run") as mock_run:
                menu.show_system_menu(back_to_exit=True)

                mock_run.assert_called_once_with(["systemctl", "reboot"])

    def test_powers_off_when_shutdown_selected(self):
        with patch("menu.show_fuzzel_menu", return_value="󰐥  Shutdown"):
            with patch("menu.subprocess.run") as mock_run:
                menu.show_system_menu(back_to_exit=True)

                mock_run.assert_called_once_with(["systemctl", "poweroff"])


class TestShowStyleMenu:
    def test_opens_theme_menu_when_theme_selected(self):
        with patch("menu.show_fuzzel_menu", return_value="󰸌  Theme"):
            with patch("menu.show_theme_menu") as mock_theme:
                menu.show_style_menu(back_to_exit=True)

                mock_theme.assert_called_once_with(True)

    def test_changes_background_when_background_selected(self):
        with patch("menu.show_fuzzel_menu", return_value="  Background"):
            with patch("menu.subprocess.run") as mock_run:
                menu.show_style_menu(back_to_exit=True)

                mock_run.assert_called_once_with(["hypr-theme-bg-next"])


class TestGoToMenu:
    def test_launches_fuzzel_for_apps(self):
        with patch("menu.subprocess.run") as mock_run:
            menu.go_to_menu("󰀻  Apps", back_to_exit=True)

            mock_run.assert_called_once_with(["hypr-fuzzel"])

    def test_opens_style_menu_for_style(self):
        with patch("menu.show_style_menu") as mock_style:
            menu.go_to_menu("  Style", back_to_exit=True)

            mock_style.assert_called_once_with(True)

    def test_opens_system_menu_for_system(self):
        with patch("menu.show_system_menu") as mock_system:
            menu.go_to_menu("  System", back_to_exit=True)

            mock_system.assert_called_once_with(True)


class TestMain:
    def test_goes_to_menu_with_argument(self):
        with patch("menu.sys.argv", ["cmd", "apps"]):
            with patch("menu.go_to_menu") as mock_go:
                menu.main()

                mock_go.assert_called_once_with("apps", back_to_exit=True)

    def test_shows_main_menu_without_arguments(self):
        with patch("menu.sys.argv", ["cmd"]):
            with patch("menu.show_main_menu") as mock_main:
                menu.main()

                mock_main.assert_called_once_with(back_to_exit=False)
