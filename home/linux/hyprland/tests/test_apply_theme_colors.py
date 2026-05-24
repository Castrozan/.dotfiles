from unittest.mock import MagicMock, call, patch

import apply_theme_colors


class TestIsHyprctlConnected:
    def test_returns_true_when_hyprctl_succeeds(self):
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("apply_theme_colors.subprocess.run", return_value=mock_result):
            assert apply_theme_colors.is_hyprctl_connected() is True

    def test_returns_false_when_hyprctl_fails(self):
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("apply_theme_colors.subprocess.run", return_value=mock_result):
            assert apply_theme_colors.is_hyprctl_connected() is False


class TestEnsureHyprctlConnected:
    def test_returns_true_when_already_connected(self):
        with patch(
            "apply_theme_colors.is_hyprctl_connected",
            return_value=True,
        ):
            assert apply_theme_colors.ensure_hyprctl_connected() is True

    def test_falls_back_to_socket_search_when_not_connected(self):
        with patch(
            "apply_theme_colors.is_hyprctl_connected",
            return_value=False,
        ):
            with patch(
                "apply_theme_colors.find_live_hyprland_socket",
                return_value=True,
            ):
                assert apply_theme_colors.ensure_hyprctl_connected() is True

    def test_returns_false_when_nothing_works(self):
        with patch(
            "apply_theme_colors.is_hyprctl_connected",
            return_value=False,
        ):
            with patch(
                "apply_theme_colors.find_live_hyprland_socket",
                return_value=False,
            ):
                assert apply_theme_colors.ensure_hyprctl_connected() is False

    def test_does_not_search_sockets_when_already_connected(self):
        with patch(
            "apply_theme_colors.is_hyprctl_connected",
            return_value=True,
        ):
            with patch(
                "apply_theme_colors.find_live_hyprland_socket",
            ) as mock_find:
                apply_theme_colors.ensure_hyprctl_connected()
                mock_find.assert_not_called()


class TestApplyThemeBorderColorsFromConfig:
    def test_applies_color_to_both_hyprctl_keywords(self, tmp_path):
        config_file = tmp_path / "hyprland.conf"
        config_file.write_text("general {\n    col.active_border = rgb(7aa2f7)\n}\n")

        with patch.object(apply_theme_colors, "THEME_HYPRLAND_CONF", config_file):
            with patch("apply_theme_colors.subprocess.run") as mock_run:
                apply_theme_colors.apply_theme_border_colors_from_config()

                assert mock_run.call_count == 2
                assert mock_run.call_args_list[0] == call(
                    [
                        "hyprctl",
                        "keyword",
                        "general:col.active_border",
                        "rgb(7aa2f7)",
                    ],
                    capture_output=True,
                )
                assert mock_run.call_args_list[1] == call(
                    [
                        "hyprctl",
                        "keyword",
                        "group:col.border_active",
                        "rgb(7aa2f7)",
                    ],
                    capture_output=True,
                )

    def test_uses_first_rgb_match_from_config(self, tmp_path):
        config_file = tmp_path / "hyprland.conf"
        config_file.write_text(
            "col.active_border = rgb(ff0000)\ncol.inactive_border = rgb(333333)\n"
        )

        with patch.object(apply_theme_colors, "THEME_HYPRLAND_CONF", config_file):
            with patch("apply_theme_colors.subprocess.run") as mock_run:
                apply_theme_colors.apply_theme_border_colors_from_config()

                assert mock_run.call_args_list[0] == call(
                    [
                        "hyprctl",
                        "keyword",
                        "general:col.active_border",
                        "rgb(ff0000)",
                    ],
                    capture_output=True,
                )

    def test_does_nothing_when_config_file_missing(self, tmp_path):
        missing_file = tmp_path / "nonexistent.conf"

        with patch.object(apply_theme_colors, "THEME_HYPRLAND_CONF", missing_file):
            with patch("apply_theme_colors.subprocess.run") as mock_run:
                apply_theme_colors.apply_theme_border_colors_from_config()

                mock_run.assert_not_called()

    def test_does_nothing_when_no_rgb_color_in_config(self, tmp_path):
        config_file = tmp_path / "hyprland.conf"
        config_file.write_text("general {\n    some_setting = value\n}\n")

        with patch.object(apply_theme_colors, "THEME_HYPRLAND_CONF", config_file):
            with patch("apply_theme_colors.subprocess.run") as mock_run:
                apply_theme_colors.apply_theme_border_colors_from_config()

                mock_run.assert_not_called()


class TestMain:
    def test_applies_colors_when_hyprctl_connected(self):
        with patch(
            "apply_theme_colors.ensure_hyprctl_connected",
            return_value=True,
        ):
            with patch(
                "apply_theme_colors.apply_theme_border_colors_from_config"
            ) as mock_apply:
                apply_theme_colors.main()

                mock_apply.assert_called_once()

    def test_does_nothing_when_hyprctl_not_connected(self):
        with patch(
            "apply_theme_colors.ensure_hyprctl_connected",
            return_value=False,
        ):
            with patch(
                "apply_theme_colors.apply_theme_border_colors_from_config"
            ) as mock_apply:
                apply_theme_colors.main()

                mock_apply.assert_not_called()
