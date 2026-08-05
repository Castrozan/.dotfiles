import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: themeColors

        function parseThemeColors(jsonText) {
            try {
                return JSON.parse(jsonText);
            } catch (error) {
                return null;
            }
        }

        function rgbStringToQtColor(rgbString, alpha) {
            var parts = rgbString.split(",");
            if (parts.length !== 3)
                return Qt.rgba(0, 0, 0, alpha);
            return Qt.rgba(parseInt(parts[0].trim()) / 255.0, parseInt(parts[1].trim()) / 255.0, parseInt(parts[2].trim()) / 255.0, alpha);
        }
    }

    TestCase {
        name: "ThemeColorsParseThemeColors"

        function test_parses_valid_json() {
            var result = themeColors.parseThemeColors('{"background": "#1e1e2e", "foreground": "#cdd6f4"}');
            verify(result !== null);
            compare(result.background, "#1e1e2e");
            compare(result.foreground, "#cdd6f4");
        }

        function test_returns_null_for_invalid_json() {
            compare(themeColors.parseThemeColors("not json"), null);
        }

        function test_returns_null_for_empty_string() {
            compare(themeColors.parseThemeColors(""), null);
        }

        function test_handles_all_theme_fields() {
            var json = JSON.stringify({
                background: "#1e1e2e",
                backgroundRgb: "30,30,46",
                foreground: "#cdd6f4",
                accent: "#94e2d5",
                warning: "#f9e2af",
                error: "#f38ba8",
                secondary: "#f5c2e7",
                surface: "#45475a",
                surfaceRgb: "69,71,90",
                primary: "#89b4fa",
                dim: "#6c7086"
            });
            var result = themeColors.parseThemeColors(json);
            verify(result !== null);
            compare(result.accent, "#94e2d5");
            compare(result.backgroundRgb, "30,30,46");
            compare(result.dim, "#6c7086");
        }
    }

    TestCase {
        name: "ThemeColorsRgbStringToQtColor"

        function test_converts_rgb_string_to_color() {
            var color = themeColors.rgbStringToQtColor("255,128,0", 1.0);
            fuzzyCompare(color.r, 1.0, 0.01);
            fuzzyCompare(color.g, 0.502, 0.01);
            fuzzyCompare(color.b, 0.0, 0.01);
            fuzzyCompare(color.a, 1.0, 0.01);
        }

        function test_applies_alpha() {
            var color = themeColors.rgbStringToQtColor("30,30,46", 0.85);
            fuzzyCompare(color.a, 0.85, 0.01);
        }

        function test_returns_black_for_invalid_rgb() {
            var color = themeColors.rgbStringToQtColor("invalid", 1.0);
            fuzzyCompare(color.r, 0.0, 0.01);
            fuzzyCompare(color.g, 0.0, 0.01);
            fuzzyCompare(color.b, 0.0, 0.01);
        }

        function test_handles_spaces_in_rgb_string() {
            var color = themeColors.rgbStringToQtColor("  255 , 128 , 0  ", 1.0);
            fuzzyCompare(color.r, 1.0, 0.01);
            fuzzyCompare(color.g, 0.502, 0.01);
        }

        function test_zero_rgb_produces_black() {
            var color = themeColors.rgbStringToQtColor("0,0,0", 1.0);
            fuzzyCompare(color.r, 0.0, 0.01);
            fuzzyCompare(color.g, 0.0, 0.01);
            fuzzyCompare(color.b, 0.0, 0.01);
        }

        function test_max_rgb_produces_white() {
            var color = themeColors.rgbStringToQtColor("255,255,255", 1.0);
            fuzzyCompare(color.r, 1.0, 0.01);
            fuzzyCompare(color.g, 1.0, 0.01);
            fuzzyCompare(color.b, 1.0, 0.01);
        }
    }
}
