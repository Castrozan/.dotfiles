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
