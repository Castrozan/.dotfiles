from unittest.mock import patch

import apply_theme_colors


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
