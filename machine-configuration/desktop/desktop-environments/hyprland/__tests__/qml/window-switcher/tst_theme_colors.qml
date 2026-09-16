import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

    TestCase {
        name: "WindowSwitcherThemeColors"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_parse_valid_theme_colors() {
            var json = '{"backgroundRgb": "26, 27, 38", "foreground": "#c0caf5", "accent": "#7aa2f7"}';
            var result = windowSwitcher.parseThemeColors(json);
            verify(result !== null);
            compare(result.backgroundRgb, "26, 27, 38");
        }

        function test_parse_invalid_theme_returns_null() {
            compare(windowSwitcher.parseThemeColors("not json"), null);
        }

        function test_rgb_string_to_color_valid() {
            var c = windowSwitcher.rgbStringToQtColor("255, 128, 0", 0.5);
            verify(Math.abs(c.r - 1.0) < 0.01);
            verify(Math.abs(c.g - 0.502) < 0.01);
            verify(Math.abs(c.b - 0.0) < 0.01);
            verify(Math.abs(c.a - 0.5) < 0.01);
        }

        function test_rgb_string_invalid_returns_black() {
            var c = windowSwitcher.rgbStringToQtColor("invalid", 0.85);
            compare(c.r, 0);
            compare(c.g, 0);
            compare(c.b, 0);
            verify(Math.abs(c.a - 0.85) < 0.01);
        }
    }
}
