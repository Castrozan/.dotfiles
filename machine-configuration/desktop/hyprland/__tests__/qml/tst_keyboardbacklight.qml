import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: keyboardBacklight

        property int brightnessLevel: 2
        readonly property var levels: [0, 5, 25, 50, 100]
        readonly property var levelIcons: ["󰌐", "󰌌", "󰌌", "󰌌", "󰌌"]
        readonly property var levelOpacities: [0.3, 0.4, 0.6, 0.8, 1.0]

        function cycleBrightness() {
            brightnessLevel = (brightnessLevel + 1) % levels.length;
        }

        function currentBrightnessPercent() {
            return levels[brightnessLevel];
        }

        function currentIcon() {
            return levelIcons[brightnessLevel];
        }

        function currentOpacity() {
            return levelOpacities[brightnessLevel];
        }
    }

    TestCase {
        name: "KeyboardBacklightLevels"

        function test_levels_array_has_five_entries() {
            compare(keyboardBacklight.levels.length, 5);
        }

        function test_levels_start_at_zero() {
            compare(keyboardBacklight.levels[0], 0);
        }

        function test_levels_end_at_100() {
            compare(keyboardBacklight.levels[4], 100);
        }

        function test_levels_are_ascending() {
            for (var i = 1; i < keyboardBacklight.levels.length; i++) {
                verify(keyboardBacklight.levels[i] > keyboardBacklight.levels[i - 1]);
            }
        }

        function test_icons_array_matches_levels_length() {
            compare(keyboardBacklight.levelIcons.length, keyboardBacklight.levels.length);
        }

        function test_opacities_array_matches_levels_length() {
            compare(keyboardBacklight.levelOpacities.length, keyboardBacklight.levels.length);
        }

        function test_opacities_are_ascending() {
            for (var i = 1; i < keyboardBacklight.levelOpacities.length; i++) {
                verify(keyboardBacklight.levelOpacities[i] > keyboardBacklight.levelOpacities[i - 1]);
            }
        }

        function test_all_opacities_between_zero_and_one() {
            for (var i = 0; i < keyboardBacklight.levelOpacities.length; i++) {
                verify(keyboardBacklight.levelOpacities[i] > 0);
                verify(keyboardBacklight.levelOpacities[i] <= 1.0);
            }
        }
    }

    TestCase {
        name: "KeyboardBacklightCycling"

        function init() {
            keyboardBacklight.brightnessLevel = 0;
        }

        function test_default_starts_at_level_zero_after_init() {
            compare(keyboardBacklight.brightnessLevel, 0);
            compare(keyboardBacklight.currentBrightnessPercent(), 0);
        }

        function test_cycle_from_zero_goes_to_five() {
            keyboardBacklight.cycleBrightness();
            compare(keyboardBacklight.currentBrightnessPercent(), 5);
        }

        function test_cycle_through_all_levels() {
            compare(keyboardBacklight.currentBrightnessPercent(), 0);
            keyboardBacklight.cycleBrightness();
            compare(keyboardBacklight.currentBrightnessPercent(), 5);
            keyboardBacklight.cycleBrightness();
            compare(keyboardBacklight.currentBrightnessPercent(), 25);
            keyboardBacklight.cycleBrightness();
            compare(keyboardBacklight.currentBrightnessPercent(), 50);
            keyboardBacklight.cycleBrightness();
            compare(keyboardBacklight.currentBrightnessPercent(), 100);
        }

        function test_cycle_wraps_around_to_zero() {
            keyboardBacklight.brightnessLevel = 4;
            compare(keyboardBacklight.currentBrightnessPercent(), 100);
            keyboardBacklight.cycleBrightness();
            compare(keyboardBacklight.currentBrightnessPercent(), 0);
        }

        function test_off_level_uses_distinct_icon() {
            keyboardBacklight.brightnessLevel = 0;
            compare(keyboardBacklight.currentIcon(), "󰌐");
        }

        function test_on_levels_use_same_icon() {
            for (var i = 1; i < keyboardBacklight.levels.length; i++) {
                keyboardBacklight.brightnessLevel = i;
                compare(keyboardBacklight.currentIcon(), "󰌌");
            }
        }

        function test_off_level_has_lowest_opacity() {
            keyboardBacklight.brightnessLevel = 0;
            var offOpacity = keyboardBacklight.currentOpacity();
            for (var i = 1; i < keyboardBacklight.levels.length; i++) {
                keyboardBacklight.brightnessLevel = i;
                verify(keyboardBacklight.currentOpacity() > offOpacity);
            }
        }
    }
}
