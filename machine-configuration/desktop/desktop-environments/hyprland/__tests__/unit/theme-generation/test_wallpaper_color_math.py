import pytest

import wallpaper_color_math as color_math


class TestCalculateYiqLuminance:
    def test_black_has_zero_luminance(self):
        assert color_math.calculate_yiq_luminance(0, 0, 0) == 0

    def test_white_has_maximum_luminance(self):
        assert color_math.calculate_yiq_luminance(255, 255, 255) == 255

    def test_green_has_higher_luminance_than_blue(self):
        green_luminance = color_math.calculate_yiq_luminance(0, 255, 0)
        blue_luminance = color_math.calculate_yiq_luminance(0, 0, 255)
        assert green_luminance > blue_luminance


class TestDarkenColor:
    def test_darken_by_zero_returns_black(self):
        assert color_math.darken_color_by_percentage((100, 200, 50), 0.0) == (0, 0, 0)

    def test_darken_by_one_returns_same(self):
        assert color_math.darken_color_by_percentage((100, 200, 50), 1.0) == (
            100,
            200,
            50,
        )

    def test_darken_halves_values(self):
        assert color_math.darken_color_by_percentage((100, 200, 50), 0.5) == (
            50,
            100,
            25,
        )


class TestLightenColor:
    def test_lighten_by_zero_returns_same(self):
        assert color_math.lighten_color_by_percentage((100, 100, 100), 0.0) == (
            100,
            100,
            100,
        )

    def test_lighten_by_one_returns_white(self):
        result = color_math.lighten_color_by_percentage((100, 100, 100), 1.0)
        assert result == (255, 255, 255)


class TestHueDistance:
    def test_same_hue_is_zero(self):
        assert color_math.hue_distance(0.5, 0.5) == 0.0

    def test_opposite_hues_is_half(self):
        assert color_math.hue_distance(0.0, 0.5) == 0.5

    def test_wraps_around_hue_circle(self):
        assert color_math.hue_distance(0.9, 0.1) == pytest.approx(0.2)

    def test_red_is_close_to_near_red(self):
        assert color_math.hue_distance(0.0, 0.05) == pytest.approx(0.05)


class TestSaturateAndBrightenColor:
    def test_increases_saturation(self):
        muted_green = (80, 100, 80)
        result = color_math.saturate_and_brighten_color(
            muted_green, saturation_boost=0.8, target_lightness=0.45
        )
        original_saturation = color_math.color_to_hls(muted_green)[2]
        result_saturation = color_math.color_to_hls(result)[2]
        assert result_saturation > original_saturation

    def test_preserves_hue(self):
        green = (40, 160, 60)
        result = color_math.saturate_and_brighten_color(
            green, saturation_boost=0.6, target_lightness=0.45
        )
        original_hue = color_math.color_to_hls(green)[0]
        result_hue = color_math.color_to_hls(result)[0]
        assert abs(original_hue - result_hue) < 0.01


class TestFormatRgbAsHexString:
    def test_formats_black(self):
        assert color_math.format_rgb_as_hex_string((0, 0, 0)) == "#000000"

    def test_formats_white(self):
        assert color_math.format_rgb_as_hex_string((255, 255, 255)) == "#ffffff"

    def test_formats_red(self):
        assert color_math.format_rgb_as_hex_string((255, 0, 0)) == "#ff0000"
