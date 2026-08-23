from unittest.mock import call, patch

import hyprland_theme


class TestApplyThemeBorderColorsFromConfig:
    def test_applies_the_color_to_both_hyprctl_keywords(self, tmp_path):
        config_file = tmp_path / "hyprland.conf"
        config_file.write_text("general {\n    col.active_border = rgb(7aa2f7)\n}\n")

        with patch.object(hyprland_theme, "THEME_HYPRLAND_CONF", config_file):
            with patch("hyprland_theme.subprocess.run") as mock_run:
                hyprland_theme.apply_theme_border_colors_from_config()

                assert mock_run.call_args_list == [
                    call(
                        [
                            "hyprctl",
                            "keyword",
                            "general:col.active_border",
                            "rgb(7aa2f7)",
                        ],
                        capture_output=True,
                    ),
                    call(
                        [
                            "hyprctl",
                            "keyword",
                            "group:col.border_active",
                            "rgb(7aa2f7)",
                        ],
                        capture_output=True,
                    ),
                ]

    def test_uses_the_first_rgb_match_in_the_config(self, tmp_path):
        config_file = tmp_path / "hyprland.conf"
        config_file.write_text(
            "col.active_border = rgb(ff0000)\ncol.inactive_border = rgb(333333)\n"
        )

        with patch.object(hyprland_theme, "THEME_HYPRLAND_CONF", config_file):
            with patch("hyprland_theme.subprocess.run") as mock_run:
                hyprland_theme.apply_theme_border_colors_from_config()

                assert mock_run.call_args_list[0] == call(
                    ["hyprctl", "keyword", "general:col.active_border", "rgb(ff0000)"],
                    capture_output=True,
                )

    def test_does_nothing_when_the_config_is_missing(self, tmp_path):
        with patch.object(
            hyprland_theme, "THEME_HYPRLAND_CONF", tmp_path / "nonexistent.conf"
        ):
            with patch("hyprland_theme.subprocess.run") as mock_run:
                hyprland_theme.apply_theme_border_colors_from_config()

                mock_run.assert_not_called()

    def test_does_nothing_when_the_config_carries_no_rgb_color(self, tmp_path):
        config_file = tmp_path / "hyprland.conf"
        config_file.write_text("general {\n    some_setting = value\n}\n")

        with patch.object(hyprland_theme, "THEME_HYPRLAND_CONF", config_file):
            with patch("hyprland_theme.subprocess.run") as mock_run:
                hyprland_theme.apply_theme_border_colors_from_config()

                mock_run.assert_not_called()
