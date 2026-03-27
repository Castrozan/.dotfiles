import re
import sys
from unittest.mock import MagicMock, patch

import pytest

mock_colorthief_module = MagicMock()
mock_pil_module = MagicMock()
mock_pil_image_module = MagicMock()
sys.modules["colorthief"] = mock_colorthief_module
sys.modules["PIL"] = mock_pil_module
sys.modules["PIL.Image"] = mock_pil_image_module

import theme_generate_from_wallpaper  # noqa: E402


SAMPLE_EIGHT_COLORS = [
    (30, 30, 40),
    (180, 50, 50),
    (50, 150, 80),
    (200, 180, 100),
    (80, 120, 200),
    (150, 100, 180),
    (80, 160, 140),
    (200, 200, 180),
]


class TestCalculateYiqLuminance:
    def test_black_has_zero_luminance(self):
        assert theme_generate_from_wallpaper.calculate_yiq_luminance(0, 0, 0) == 0

    def test_white_has_maximum_luminance(self):
        assert (
            theme_generate_from_wallpaper.calculate_yiq_luminance(255, 255, 255)
            == 255.0
        )

    def test_green_contributes_most_to_luminance(self):
        green_luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
            0, 255, 0
        )
        red_luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(255, 0, 0)
        blue_luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
            0, 0, 255
        )
        assert green_luminance > red_luminance > blue_luminance

    def test_yiq_formula_uses_correct_coefficients(self):
        result = theme_generate_from_wallpaper.calculate_yiq_luminance(100, 100, 100)
        expected = (100 * 299 + 100 * 587 + 100 * 114) / 1000
        assert result == expected


class TestDarkenColorByPercentage:
    def test_darken_by_half(self):
        result = theme_generate_from_wallpaper.darken_color_by_percentage(
            (200, 100, 50), 0.5
        )
        assert result == (100, 50, 25)

    def test_darken_to_black(self):
        result = theme_generate_from_wallpaper.darken_color_by_percentage(
            (200, 100, 50), 0.0
        )
        assert result == (0, 0, 0)

    def test_no_darkening_preserves_color(self):
        result = theme_generate_from_wallpaper.darken_color_by_percentage(
            (200, 100, 50), 1.0
        )
        assert result == (200, 100, 50)


class TestLightenColorByPercentage:
    def test_lighten_by_half(self):
        result = theme_generate_from_wallpaper.lighten_color_by_percentage(
            (100, 100, 100), 0.5
        )
        assert result == (177, 177, 177)

    def test_lighten_to_white(self):
        result = theme_generate_from_wallpaper.lighten_color_by_percentage(
            (100, 100, 100), 1.0
        )
        assert result == (255, 255, 255)

    def test_no_lightening_preserves_color(self):
        result = theme_generate_from_wallpaper.lighten_color_by_percentage(
            (100, 100, 100), 0.0
        )
        assert result == (100, 100, 100)


class TestBuildSixteenColorPalette:
    def test_produces_sixteen_colors(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_EIGHT_COLORS
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        assert len(palette) == 16

    def test_first_color_is_darkened_version_of_darkest(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_EIGHT_COLORS
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        expected = theme_generate_from_wallpaper.darken_color_by_percentage(
            sorted_colors[0], 0.2
        )
        assert palette[0] == expected

    def test_color7_is_lightened_version_of_brightest(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_EIGHT_COLORS
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        expected = theme_generate_from_wallpaper.lighten_color_by_percentage(
            sorted_colors[7], 0.60
        )
        assert palette[7] == expected

    def test_color15_equals_color7(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_EIGHT_COLORS
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        assert palette[15] == palette[7]

    def test_color8_is_lightened_version_of_color0(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_EIGHT_COLORS
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        expected = theme_generate_from_wallpaper.lighten_color_by_percentage(
            palette[0], 0.25
        )
        assert palette[8] == expected


class TestGenerateColorsTomlFromPalette:
    @pytest.fixture
    def sample_toml_output(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_EIGHT_COLORS
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        return theme_generate_from_wallpaper.generate_colors_toml_from_palette(palette)

    def test_contains_all_required_keys(self, sample_toml_output):
        required_keys = [
            "accent",
            "cursor",
            "foreground",
            "background",
            "selection_foreground",
            "selection_background",
        ]
        for key in required_keys:
            assert f'{key} = "' in sample_toml_output

    def test_contains_all_sixteen_color_keys(self, sample_toml_output):
        for index in range(16):
            assert f'color{index} = "' in sample_toml_output

    def test_all_values_are_valid_hex_format(self, sample_toml_output):
        hex_values = re.findall(r'"(#[0-9a-f]{6})"', sample_toml_output)
        assert len(hex_values) == 22

    def test_ends_with_newline(self, sample_toml_output):
        assert sample_toml_output.endswith("\n")


class TestPickMostSaturatedAccentColor:
    def test_picks_most_saturated_from_candidates(self):
        palette = [
            (0, 0, 0),
            (128, 128, 128),
            (255, 0, 0),
            (100, 100, 100),
            (50, 50, 50),
            (200, 200, 200),
            (150, 150, 150),
            (255, 255, 255),
        ] + [(0, 0, 0)] * 8
        result = theme_generate_from_wallpaper.pick_most_saturated_accent_color(palette)
        assert result == (255, 0, 0)

    def test_only_considers_indices_one_through_six(self):
        palette = [
            (255, 0, 0),
            (128, 128, 128),
            (130, 130, 130),
            (132, 132, 132),
            (134, 134, 134),
            (136, 136, 136),
            (138, 138, 138),
            (0, 255, 0),
        ] + [(0, 0, 0)] * 8
        result = theme_generate_from_wallpaper.pick_most_saturated_accent_color(palette)
        assert result != (255, 0, 0)
        assert result != (0, 255, 0)


class TestExtractFirstFrameIfGif:
    def test_returns_original_path_for_non_gif(self):
        mock_image = MagicMock()
        mock_image.format = "PNG"
        mock_image.__enter__ = MagicMock(return_value=mock_image)
        mock_image.__exit__ = MagicMock(return_value=False)

        with patch.object(mock_pil_image_module, "open", return_value=mock_image):
            with patch.object(
                theme_generate_from_wallpaper, "Image", mock_pil_image_module
            ):
                result = theme_generate_from_wallpaper.extract_first_frame_if_gif(
                    MagicMock(spec=type(MagicMock()))
                )
                assert result is not None

    def test_saves_first_frame_for_gif(self):
        mock_image = MagicMock()
        mock_image.format = "GIF"
        mock_image.__enter__ = MagicMock(return_value=mock_image)
        mock_image.__exit__ = MagicMock(return_value=False)

        with patch.object(mock_pil_image_module, "open", return_value=mock_image):
            with patch.object(
                theme_generate_from_wallpaper, "Image", mock_pil_image_module
            ):
                theme_generate_from_wallpaper.extract_first_frame_if_gif(
                    MagicMock(spec=type(MagicMock()))
                )
                mock_image.seek.assert_called_once_with(0)
                mock_image.save.assert_called_once()


class TestFormatRgbAsHexString:
    def test_formats_black(self):
        assert (
            theme_generate_from_wallpaper.format_rgb_as_hex_string((0, 0, 0))
            == "#000000"
        )

    def test_formats_white(self):
        assert (
            theme_generate_from_wallpaper.format_rgb_as_hex_string((255, 255, 255))
            == "#ffffff"
        )

    def test_formats_arbitrary_color(self):
        assert (
            theme_generate_from_wallpaper.format_rgb_as_hex_string((126, 156, 216))
            == "#7e9cd8"
        )


class TestSortColorsByLuminance:
    def test_sorts_darkest_first(self):
        colors = [(255, 255, 255), (0, 0, 0), (128, 128, 128)]
        result = theme_generate_from_wallpaper.sort_colors_by_luminance(colors)
        assert result[0] == (0, 0, 0)
        assert result[-1] == (255, 255, 255)

    def test_preserves_all_colors(self):
        colors = [(200, 50, 50), (50, 200, 50), (50, 50, 200)]
        result = theme_generate_from_wallpaper.sort_colors_by_luminance(colors)
        assert len(result) == 3
        assert set(result) == set(colors)
