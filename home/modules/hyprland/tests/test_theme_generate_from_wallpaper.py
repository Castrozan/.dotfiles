import colorsys
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

colorthief_mock = ModuleType("colorthief")
colorthief_mock.ColorThief = MagicMock
sys.modules.setdefault("colorthief", colorthief_mock)

pil_mock = ModuleType("PIL")
pil_image_mock = ModuleType("PIL.Image")
pil_mock.Image = pil_image_mock
sys.modules.setdefault("PIL", pil_mock)
sys.modules.setdefault("PIL.Image", pil_image_mock)

import theme_generate_from_wallpaper

SAMPLE_COLORFUL_PALETTE = [
    (20, 10, 10),
    (180, 40, 40),
    (40, 160, 60),
    (180, 170, 40),
    (40, 60, 180),
    (160, 40, 170),
    (40, 170, 170),
    (200, 200, 190),
]


class TestCalculateYiqLuminance:
    def test_black_has_zero_luminance(self):
        assert theme_generate_from_wallpaper.calculate_yiq_luminance(0, 0, 0) == 0

    def test_white_has_maximum_luminance(self):
        assert (
            theme_generate_from_wallpaper.calculate_yiq_luminance(255, 255, 255) == 255
        )

    def test_green_has_higher_luminance_than_blue(self):
        green_luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
            0, 255, 0
        )
        blue_luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
            0, 0, 255
        )
        assert green_luminance > blue_luminance


class TestSortColorsByLuminance:
    def test_sorts_darkest_first(self):
        colors = [(255, 255, 255), (0, 0, 0), (128, 128, 128)]
        result = theme_generate_from_wallpaper.sort_colors_by_luminance(colors)
        assert result[0] == (0, 0, 0)
        assert result[-1] == (255, 255, 255)

    def test_preserves_length(self):
        colors = [(10, 20, 30), (40, 50, 60)]
        result = theme_generate_from_wallpaper.sort_colors_by_luminance(colors)
        assert len(result) == 2


class TestDarkenColor:
    def test_darken_by_zero_returns_black(self):
        assert theme_generate_from_wallpaper.darken_color_by_percentage(
            (100, 200, 50), 0.0
        ) == (0, 0, 0)

    def test_darken_by_one_returns_same(self):
        assert theme_generate_from_wallpaper.darken_color_by_percentage(
            (100, 200, 50), 1.0
        ) == (100, 200, 50)

    def test_darken_halves_values(self):
        assert theme_generate_from_wallpaper.darken_color_by_percentage(
            (100, 200, 50), 0.5
        ) == (50, 100, 25)


class TestLightenColor:
    def test_lighten_by_zero_returns_same(self):
        assert theme_generate_from_wallpaper.lighten_color_by_percentage(
            (100, 100, 100), 0.0
        ) == (100, 100, 100)

    def test_lighten_by_one_returns_white(self):
        result = theme_generate_from_wallpaper.lighten_color_by_percentage(
            (100, 100, 100), 1.0
        )
        assert result == (255, 255, 255)


class TestHueDistance:
    def test_same_hue_is_zero(self):
        assert theme_generate_from_wallpaper.hue_distance(0.5, 0.5) == 0.0

    def test_opposite_hues_is_half(self):
        assert theme_generate_from_wallpaper.hue_distance(0.0, 0.5) == 0.5

    def test_wraps_around_hue_circle(self):
        assert theme_generate_from_wallpaper.hue_distance(0.9, 0.1) == pytest.approx(
            0.2
        )

    def test_red_is_close_to_near_red(self):
        assert theme_generate_from_wallpaper.hue_distance(0.0, 0.05) == pytest.approx(
            0.05
        )


class TestFindClosestColorByHue:
    def test_finds_reddish_color_for_red_target(self):
        colors = [(200, 50, 50), (50, 200, 50), (50, 50, 200)]
        result = theme_generate_from_wallpaper.find_closest_color_by_hue(0.0, colors)
        assert result == (200, 50, 50)

    def test_finds_greenish_color_for_green_target(self):
        colors = [(200, 50, 50), (50, 200, 50), (50, 50, 200)]
        result = theme_generate_from_wallpaper.find_closest_color_by_hue(0.333, colors)
        assert result == (50, 200, 50)

    def test_finds_bluish_color_for_blue_target(self):
        colors = [(200, 50, 50), (50, 200, 50), (50, 50, 200)]
        result = theme_generate_from_wallpaper.find_closest_color_by_hue(0.667, colors)
        assert result == (50, 50, 200)


class TestAssignColorsToAnsiSlotsByHue:
    def test_assigns_all_six_ansi_slots(self):
        colors = SAMPLE_COLORFUL_PALETTE
        assigned = theme_generate_from_wallpaper.assign_colors_to_ansi_slots_by_hue(
            colors
        )
        assert set(assigned.keys()) == {1, 2, 3, 4, 5, 6}

    def test_red_slot_gets_reddish_color(self):
        colors = SAMPLE_COLORFUL_PALETTE
        assigned = theme_generate_from_wallpaper.assign_colors_to_ansi_slots_by_hue(
            colors
        )
        red_hue = theme_generate_from_wallpaper.color_to_hls(assigned[1])[0]
        assert theme_generate_from_wallpaper.hue_distance(red_hue, 0.0) < 0.15

    def test_green_slot_gets_greenish_color(self):
        colors = SAMPLE_COLORFUL_PALETTE
        assigned = theme_generate_from_wallpaper.assign_colors_to_ansi_slots_by_hue(
            colors
        )
        green_hue = theme_generate_from_wallpaper.color_to_hls(assigned[2])[0]
        assert theme_generate_from_wallpaper.hue_distance(green_hue, 0.333) < 0.15

    def test_prefers_chromatic_colors_over_grays(self):
        colors = [(128, 128, 128), (200, 50, 50), (127, 127, 127)]
        assigned = theme_generate_from_wallpaper.assign_colors_to_ansi_slots_by_hue(
            colors
        )
        for _slot, color in assigned.items():
            assert color == (200, 50, 50)

    def test_falls_back_to_all_colors_when_too_few_chromatic(self):
        colors = [(128, 128, 128), (127, 127, 127), (126, 126, 126)]
        assigned = theme_generate_from_wallpaper.assign_colors_to_ansi_slots_by_hue(
            colors
        )
        assert len(assigned) == 6


class TestSaturateAndBrightenColor:
    def test_increases_saturation(self):
        muted_green = (80, 100, 80)
        result = theme_generate_from_wallpaper.saturate_and_brighten_color(
            muted_green, saturation_boost=0.8, target_lightness=0.45
        )
        original_saturation = theme_generate_from_wallpaper.color_to_hls(muted_green)[2]
        result_saturation = theme_generate_from_wallpaper.color_to_hls(result)[2]
        assert result_saturation > original_saturation

    def test_preserves_hue(self):
        green = (40, 160, 60)
        result = theme_generate_from_wallpaper.saturate_and_brighten_color(
            green, saturation_boost=0.6, target_lightness=0.45
        )
        original_hue = theme_generate_from_wallpaper.color_to_hls(green)[0]
        result_hue = theme_generate_from_wallpaper.color_to_hls(result)[0]
        assert abs(original_hue - result_hue) < 0.01


class TestBuildSixteenColorPalette:
    def test_returns_sixteen_colors(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_COLORFUL_PALETTE
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        assert len(palette) == 16

    def test_color0_is_darkened(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_COLORFUL_PALETTE
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        original_luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
            *sorted_colors[0]
        )
        palette_luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
            *palette[0]
        )
        assert palette_luminance < original_luminance

    def test_color7_is_lightened(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_COLORFUL_PALETTE
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        original_luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
            *sorted_colors[-1]
        )
        palette_luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
            *palette[7]
        )
        assert palette_luminance > original_luminance

    def test_color15_is_brighter_than_color7(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_COLORFUL_PALETTE
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        luminance_7 = theme_generate_from_wallpaper.calculate_yiq_luminance(*palette[7])
        luminance_15 = theme_generate_from_wallpaper.calculate_yiq_luminance(
            *palette[15]
        )
        assert luminance_15 >= luminance_7

    def test_brights_are_brighter_than_normals(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_COLORFUL_PALETTE
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        for normal_index in [1, 2, 3, 4, 5, 6]:
            bright_index = normal_index + 8
            normal_lum = theme_generate_from_wallpaper.calculate_yiq_luminance(
                *palette[normal_index]
            )
            bright_lum = theme_generate_from_wallpaper.calculate_yiq_luminance(
                *palette[bright_index]
            )
            assert bright_lum >= normal_lum, (
                f"color{bright_index} should be brighter than color{normal_index}"
            )


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

    def test_formats_red(self):
        assert (
            theme_generate_from_wallpaper.format_rgb_as_hex_string((255, 0, 0))
            == "#ff0000"
        )


class TestGenerateColorsToml:
    def test_contains_all_required_keys(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_COLORFUL_PALETTE
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        output = theme_generate_from_wallpaper.generate_colors_toml_from_palette(
            palette
        )

        required_keys = [
            "accent",
            "cursor",
            "foreground",
            "background",
            "selection_foreground",
            "selection_background",
        ] + [f"color{i}" for i in range(16)]

        for key in required_keys:
            assert f'{key} = "#' in output, f"Missing key: {key}"

    def test_all_values_are_valid_hex(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_COLORFUL_PALETTE
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        output = theme_generate_from_wallpaper.generate_colors_toml_from_palette(
            palette
        )

        for line in output.strip().split("\n"):
            if "=" not in line:
                continue
            value = line.split("=")[1].strip().strip('"')
            assert value.startswith("#"), f"Value doesn't start with #: {value}"
            assert len(value) == 7, f"Wrong hex length: {value}"

    def test_background_is_dark(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_COLORFUL_PALETTE
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        output = theme_generate_from_wallpaper.generate_colors_toml_from_palette(
            palette
        )
        for line in output.strip().split("\n"):
            if line.startswith("background"):
                hex_val = line.split('"')[1]
                red = int(hex_val[1:3], 16)
                green = int(hex_val[3:5], 16)
                blue = int(hex_val[5:7], 16)
                luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
                    red, green, blue
                )
                assert luminance < 50, (
                    f"Background too bright: {hex_val} (luminance={luminance})"
                )
                break

    def test_foreground_is_bright(self):
        sorted_colors = theme_generate_from_wallpaper.sort_colors_by_luminance(
            SAMPLE_COLORFUL_PALETTE
        )
        palette = theme_generate_from_wallpaper.build_sixteen_color_palette(
            sorted_colors
        )
        output = theme_generate_from_wallpaper.generate_colors_toml_from_palette(
            palette
        )
        for line in output.strip().split("\n"):
            if line.startswith("foreground"):
                hex_val = line.split('"')[1]
                red = int(hex_val[1:3], 16)
                green = int(hex_val[3:5], 16)
                blue = int(hex_val[5:7], 16)
                luminance = theme_generate_from_wallpaper.calculate_yiq_luminance(
                    red, green, blue
                )
                assert luminance > 150, (
                    f"Foreground too dim: {hex_val} (luminance={luminance})"
                )
                break
