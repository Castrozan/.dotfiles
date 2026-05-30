import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

colorthief_mock = ModuleType("colorthief")
colorthief_mock.ColorThief = MagicMock
sys.modules.setdefault("colorthief", colorthief_mock)

pil_mock = ModuleType("PIL")
pil_image_mock = ModuleType("PIL.Image")
pil_mock.Image = pil_image_mock
sys.modules.setdefault("PIL", pil_mock)
sys.modules.setdefault("PIL.Image", pil_image_mock)

import theme_generate_from_wallpaper as generator
import wallpaper_color_math as color_math

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


@pytest.fixture
def palette():
    sorted_colors = generator.sort_colors_by_luminance(SAMPLE_COLORFUL_PALETTE)
    return generator.build_sixteen_color_palette(sorted_colors)


@pytest.fixture
def colors_toml(palette):
    return generator.generate_colors_toml_from_palette(palette)


class TestSortColorsByLuminance:
    def test_sorts_darkest_first(self):
        colors = [(255, 255, 255), (0, 0, 0), (128, 128, 128)]
        result = generator.sort_colors_by_luminance(colors)
        assert result[0] == (0, 0, 0)
        assert result[-1] == (255, 255, 255)

    def test_preserves_length(self):
        result = generator.sort_colors_by_luminance([(10, 20, 30), (40, 50, 60)])
        assert len(result) == 2


class TestFindClosestColorByHue:
    COLORS = [(200, 50, 50), (50, 200, 50), (50, 50, 200)]

    def test_finds_reddish_color_for_red_target(self):
        assert generator.find_closest_color_by_hue(0.0, self.COLORS) == (200, 50, 50)

    def test_finds_greenish_color_for_green_target(self):
        assert generator.find_closest_color_by_hue(0.333, self.COLORS) == (50, 200, 50)

    def test_finds_bluish_color_for_blue_target(self):
        assert generator.find_closest_color_by_hue(0.667, self.COLORS) == (50, 50, 200)


class TestAssignColorsToAnsiSlotsByHue:
    def test_assigns_all_six_ansi_slots(self):
        assigned = generator.assign_colors_to_ansi_slots_by_hue(SAMPLE_COLORFUL_PALETTE)
        assert set(assigned.keys()) == {1, 2, 3, 4, 5, 6}

    def test_red_slot_gets_reddish_color(self):
        assigned = generator.assign_colors_to_ansi_slots_by_hue(SAMPLE_COLORFUL_PALETTE)
        red_hue = color_math.color_to_hls(assigned[1])[0]
        assert color_math.hue_distance(red_hue, 0.0) < 0.15

    def test_green_slot_gets_greenish_color(self):
        assigned = generator.assign_colors_to_ansi_slots_by_hue(SAMPLE_COLORFUL_PALETTE)
        green_hue = color_math.color_to_hls(assigned[2])[0]
        assert color_math.hue_distance(green_hue, 0.333) < 0.15

    def test_prefers_chromatic_colors_over_grays(self):
        colors = [(128, 128, 128), (200, 50, 50), (127, 127, 127)]
        assigned = generator.assign_colors_to_ansi_slots_by_hue(colors)
        for _slot, color in assigned.items():
            assert color == (200, 50, 50)

    def test_falls_back_to_all_colors_when_too_few_chromatic(self):
        colors = [(128, 128, 128), (127, 127, 127), (126, 126, 126)]
        assigned = generator.assign_colors_to_ansi_slots_by_hue(colors)
        assert len(assigned) == 6


class TestBuildSixteenColorPalette:
    def test_returns_sixteen_colors(self, palette):
        assert len(palette) == 16

    def test_color0_is_darkened(self, palette):
        original = color_math.calculate_yiq_luminance(*SAMPLE_COLORFUL_PALETTE[0])
        assert color_math.calculate_yiq_luminance(*palette[0]) < original

    def test_color7_is_lightened(self, palette):
        brightest = max(
            SAMPLE_COLORFUL_PALETTE,
            key=lambda c: color_math.calculate_yiq_luminance(*c),
        )
        original = color_math.calculate_yiq_luminance(*brightest)
        assert color_math.calculate_yiq_luminance(*palette[7]) > original

    def test_color15_is_brighter_than_color7(self, palette):
        luminance_7 = color_math.calculate_yiq_luminance(*palette[7])
        luminance_15 = color_math.calculate_yiq_luminance(*palette[15])
        assert luminance_15 >= luminance_7

    def test_brights_are_brighter_than_normals(self, palette):
        for normal_index in [1, 2, 3, 4, 5, 6]:
            normal = color_math.calculate_yiq_luminance(*palette[normal_index])
            bright = color_math.calculate_yiq_luminance(*palette[normal_index + 8])
            assert bright >= normal, f"color{normal_index + 8} dimmer than normal"


class TestGenerateColorsToml:
    REQUIRED_KEYS = [
        "accent",
        "cursor",
        "foreground",
        "background",
        "selection_foreground",
        "selection_background",
    ] + [f"color{i}" for i in range(16)]

    def test_contains_all_required_keys(self, colors_toml):
        for key in self.REQUIRED_KEYS:
            assert f'{key} = "#' in colors_toml, f"Missing key: {key}"

    def test_all_values_are_valid_hex(self, colors_toml):
        for line in colors_toml.strip().split("\n"):
            if "=" not in line:
                continue
            value = line.split("=")[1].strip().strip('"')
            assert value.startswith("#"), f"Value doesn't start with #: {value}"
            assert len(value) == 7, f"Wrong hex length: {value}"

    def test_background_is_dark(self, colors_toml):
        line = next(
            ln for ln in colors_toml.splitlines() if ln.startswith("background")
        )
        hex_value = line.split('"')[1]
        rgb = tuple(int(hex_value[i : i + 2], 16) for i in (1, 3, 5))
        assert color_math.calculate_yiq_luminance(*rgb) < 50

    def test_foreground_is_bright(self, colors_toml):
        line = next(
            ln for ln in colors_toml.splitlines() if ln.startswith("foreground")
        )
        hex_value = line.split('"')[1]
        rgb = tuple(int(hex_value[i : i + 2], 16) for i in (1, 3, 5))
        assert color_math.calculate_yiq_luminance(*rgb) > 150
