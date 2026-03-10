from unittest.mock import MagicMock, call, patch

import restart_hyprctl


class TestIsHyprctlConnected:
    def test_returns_true_when_hyprctl_succeeds(self):
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("restart_hyprctl.subprocess.run", return_value=mock_result):
            assert restart_hyprctl.is_hyprctl_connected() is True

    def test_returns_false_when_hyprctl_fails(self):
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("restart_hyprctl.subprocess.run", return_value=mock_result):
            assert restart_hyprctl.is_hyprctl_connected() is False


class TestFindLiveHyprlandSocket:
    def test_returns_false_when_hypr_dir_missing(self, tmp_path):
        with patch("restart_hyprctl.os.getuid", return_value=1000):
            assert restart_hyprctl.find_live_hyprland_socket() is False

    def test_returns_false_when_no_valid_socket(self, tmp_path):
        hypr_dir = tmp_path / "hypr"
        socket_dir = hypr_dir / "bad_socket"
        socket_dir.mkdir(parents=True)

        failed_result = MagicMock()
        failed_result.returncode = 1

        with patch("restart_hyprctl.os.getuid", return_value=1000):
            with patch(
                "restart_hyprctl.Path",
                return_value=hypr_dir,
            ):
                with patch(
                    "restart_hyprctl.subprocess.run",
                    return_value=failed_result,
                ):
                    assert restart_hyprctl.find_live_hyprland_socket() is False


class TestEnsureHyprctlConnected:
    def test_returns_true_when_already_connected(self):
        with patch("restart_hyprctl.is_hyprctl_connected", return_value=True):
            assert restart_hyprctl.ensure_hyprctl_connected() is True

    def test_searches_sockets_when_not_connected(self):
        with patch("restart_hyprctl.is_hyprctl_connected", return_value=False):
            with patch(
                "restart_hyprctl.find_live_hyprland_socket",
                return_value=True,
            ):
                assert restart_hyprctl.ensure_hyprctl_connected() is True

    def test_returns_false_when_no_socket_found(self):
        with patch("restart_hyprctl.is_hyprctl_connected", return_value=False):
            with patch(
                "restart_hyprctl.find_live_hyprland_socket",
                return_value=False,
            ):
                assert restart_hyprctl.ensure_hyprctl_connected() is False


class TestReloadHyprlandWithScreencopyServicesPaused:
    def test_reloads_hyprland(self):
        with patch(
            "restart_hyprctl.stop_active_screencopy_services",
            return_value=[],
        ):
            with patch("restart_hyprctl.restart_previously_stopped_services"):
                with patch("restart_hyprctl.subprocess.run") as mock_run:
                    restart_hyprctl.reload_hyprland_with_screencopy_services_paused()
                    mock_run.assert_called_once_with(["hyprctl", "reload"])


class TestApplyThemeBorderColorsFromConfig:
    def test_does_nothing_when_config_missing(self, tmp_path):
        with patch.object(
            restart_hyprctl,
            "THEME_HYPRLAND_CONF",
            tmp_path / "nonexistent.conf",
        ):
            with patch("restart_hyprctl.subprocess.run") as mock_run:
                restart_hyprctl.apply_theme_border_colors_from_config()
                mock_run.assert_not_called()

    def test_applies_border_color_from_config(self, tmp_path):
        config_file = tmp_path / "hyprland.conf"
        config_file.write_text("general:col.active_border = rgb(7e9cd8)\n")

        with patch.object(restart_hyprctl, "THEME_HYPRLAND_CONF", config_file):
            with patch("restart_hyprctl.subprocess.run") as mock_run:
                restart_hyprctl.apply_theme_border_colors_from_config()

                assert mock_run.call_count == 2
                assert mock_run.call_args_list[0] == call(
                    [
                        "hyprctl",
                        "keyword",
                        "general:col.active_border",
                        "rgb(7e9cd8)",
                    ],
                    capture_output=True,
                )
                assert mock_run.call_args_list[1] == call(
                    [
                        "hyprctl",
                        "keyword",
                        "group:col.border_active",
                        "rgb(7e9cd8)",
                    ],
                    capture_output=True,
                )

    def test_does_nothing_when_no_color_in_config(self, tmp_path):
        config_file = tmp_path / "hyprland.conf"
        config_file.write_text("some other config content\n")

        with patch.object(restart_hyprctl, "THEME_HYPRLAND_CONF", config_file):
            with patch("restart_hyprctl.subprocess.run") as mock_run:
                restart_hyprctl.apply_theme_border_colors_from_config()
                mock_run.assert_not_called()


class TestMain:
    def test_exits_early_when_not_connected(self):
        with patch(
            "restart_hyprctl.ensure_hyprctl_connected",
            return_value=False,
        ):
            with patch(
                "restart_hyprctl.reload_hyprland_with_screencopy_services_paused"
            ) as mock_reload:
                restart_hyprctl.main()
                mock_reload.assert_not_called()

    def test_reloads_and_applies_colors_when_connected(self):
        with patch(
            "restart_hyprctl.ensure_hyprctl_connected",
            return_value=True,
        ):
            with patch(
                "restart_hyprctl.reload_hyprland_with_screencopy_services_paused"
            ) as mock_reload:
                with patch(
                    "restart_hyprctl.apply_theme_border_colors_from_config"
                ) as mock_apply:
                    restart_hyprctl.main()
                    mock_reload.assert_called_once()
                    mock_apply.assert_called_once()
