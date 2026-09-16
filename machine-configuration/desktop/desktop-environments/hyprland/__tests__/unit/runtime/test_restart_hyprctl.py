from unittest.mock import patch

import restart_hyprctl


class TestReloadHyprlandWithScreencopyServicesPaused:
    def test_reloads_hyprland(self):
        with patch(
            "restart_hyprctl.stop_active_screencopy_services",
            return_value=[],
        ):
            with patch("restart_hyprctl.restart_previously_stopped_services"):
                with patch("restart_hyprctl.subprocess.run") as mock_run:
                    restart_hyprctl.reload_hyprland_config_only_with_screencopy_services_paused()
                    mock_run.assert_called_once_with(
                        ["hyprctl", "reload", "config-only"]
                    )


class TestMain:
    def test_exits_early_when_not_connected(self):
        with patch(
            "restart_hyprctl.ensure_hyprctl_connected",
            return_value=False,
        ):
            with patch(
                "restart_hyprctl.reload_hyprland_config_only_with_screencopy_services_paused"
            ) as mock_reload:
                with patch(
                    "restart_hyprctl.apply_theme_border_colors_from_config"
                ) as mock_apply:
                    restart_hyprctl.main()
                    mock_reload.assert_not_called()
                    mock_apply.assert_not_called()

    def test_reloads_and_applies_colors_when_connected(self):
        with patch(
            "restart_hyprctl.ensure_hyprctl_connected",
            return_value=True,
        ):
            with patch(
                "restart_hyprctl.reload_hyprland_config_only_with_screencopy_services_paused"
            ) as mock_reload:
                with patch(
                    "restart_hyprctl.apply_theme_border_colors_from_config"
                ) as mock_apply:
                    restart_hyprctl.main()
                    mock_reload.assert_called_once()
                    mock_apply.assert_called_once()
