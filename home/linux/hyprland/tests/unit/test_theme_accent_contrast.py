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

DARK_BLUE_DOMINANT_PALETTE = [
    (5, 7, 14),
    (18, 28, 70),
    (21, 55, 168),
    (30, 40, 120),
    (60, 70, 150),
    (40, 50, 110),
    (90, 100, 180),
    (200, 205, 220),
]

ACCENT_SLOTS = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14]


class TestCalculateContrastRatio:
    def test_black_on_white_is_maximum(self):
        ratio = color_math.calculate_contrast_ratio((0, 0, 0), (255, 255, 255))
        assert ratio == pytest.approx(21.0, abs=0.1)

    def test_identical_colors_have_ratio_one(self):
        ratio = color_math.calculate_contrast_ratio((50, 50, 50), (50, 50, 50))
        assert ratio == 1.0

    def test_is_symmetric(self):
        forward = color_math.calculate_contrast_ratio((21, 55, 168), (5, 7, 14))
        backward = color_math.calculate_contrast_ratio((5, 7, 14), (21, 55, 168))
        assert forward == backward


class TestLightenColorUntilMinimumContrast:
    def test_preserves_hue(self):
        background = (5, 7, 14)
        original = (21, 55, 168)
        lifted = color_math.lighten_color_until_minimum_contrast(
            original, background, 4.5
        )
        original_hue = color_math.color_to_hls(original)[0]
        lifted_hue = color_math.color_to_hls(lifted)[0]
        assert abs(original_hue - lifted_hue) < 0.02

    def test_reaches_target_contrast(self):
        background = (5, 7, 14)
        original = (21, 55, 168)
        lifted = color_math.lighten_color_until_minimum_contrast(
            original, background, 4.5
        )
        ratio = color_math.calculate_contrast_ratio(lifted, background)
        assert ratio >= 4.5


class TestAccentColorsMeetMinimumContrastAgainstBackground:
    def test_all_accent_slots_meet_minimum_contrast(self):
        sorted_colors = generator.sort_colors_by_luminance(DARK_BLUE_DOMINANT_PALETTE)
        palette = generator.build_sixteen_color_palette(sorted_colors)
        background = palette[0]
        floor = generator.MINIMUM_ACCENT_CONTRAST_RATIO
        for accent_slot in ACCENT_SLOTS:
            ratio = color_math.calculate_contrast_ratio(
                palette[accent_slot], background
            )
            assert ratio >= floor, (
                f"color{accent_slot} contrast {ratio:.2f} below floor"
            )

    def test_brights_remain_at_least_as_bright_as_normals(self):
        sorted_colors = generator.sort_colors_by_luminance(DARK_BLUE_DOMINANT_PALETTE)
        palette = generator.build_sixteen_color_palette(sorted_colors)
        for normal_slot in [1, 2, 3, 4, 5, 6]:
            normal_luminance = color_math.calculate_yiq_luminance(*palette[normal_slot])
            bright_luminance = color_math.calculate_yiq_luminance(
                *palette[normal_slot + 8]
            )
            assert bright_luminance >= normal_luminance
