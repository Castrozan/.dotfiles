import QtQuick
import QtTest

OnScreenDisplayFixture {
    id: root

    TestCase {
        name: "OsdContentIconSelection"

        function test_brightness_icon() {
            compare(osdContent.computeIconForType("brightness", false), "brightness_6");
        }

        function test_brightness_icon_ignores_muted() {
            compare(osdContent.computeIconForType("brightness", true), "brightness_6");
        }

        function test_mic_unmuted_icon() {
            compare(osdContent.computeIconForType("mic", false), "mic");
        }

        function test_mic_muted_icon() {
            compare(osdContent.computeIconForType("mic", true), "mic_off");
        }

        function test_volume_unmuted_icon() {
            compare(osdContent.computeIconForType("volume", false), "volume_up");
        }

        function test_volume_muted_icon() {
            compare(osdContent.computeIconForType("volume", true), "volume_off");
        }

        function test_unknown_type_defaults_to_volume_icon() {
            compare(osdContent.computeIconForType("unknown", false), "volume_up");
        }
    }
}
