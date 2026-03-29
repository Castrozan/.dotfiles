import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: osdWrapper

        property bool osdVisible: false
        property string osdType: "volume"
        property int osdValue: 0
        property bool osdMuted: false
        property bool hasReceivedSocketMessage: false

        function handleOsdMessage(message) {
            try {
                var parsed = JSON.parse(message);
                osdType = parsed.type !== undefined ? parsed.type : "volume";
                osdValue = parsed.value !== undefined ? parsed.value : 0;
                osdMuted = parsed.muted !== undefined ? parsed.muted : false;
                hasReceivedSocketMessage = true;
                return true;
            } catch (error) {
                return false;
            }
        }
    }

    QtObject {
        id: osdContent

        property string osdType: "volume"
        property int osdValue: 0
        property bool osdMuted: false

        function applyValueFromMouseY(mouseY, trackHeight) {
            var fraction = 1.0 - Math.max(0, Math.min(mouseY, trackHeight)) / trackHeight;
            return Math.round(fraction * 100);
        }

        function computeClampedFraction(value) {
            return Math.min(value / 100.0, 1.0);
        }

        function computeIconForType(type, muted) {
            if (type === "brightness") return "brightness_6";
            if (type === "mic") return muted ? "mic_off" : "mic";
            return muted ? "volume_off" : "volume_up";
        }

        function computeDisplayText(muted, value) {
            return muted ? "M" : value + "%";
        }

        function computeWheelNewValue(currentValue, angleDeltaY) {
            var delta = angleDeltaY > 0 ? 5 : -5;
            return Math.max(0, Math.min(100, currentValue + delta));
        }
    }

    TestCase {
        name: "OsdWrapperHandleMessage"

        function init() {
            osdWrapper.osdType = "volume";
            osdWrapper.osdValue = 0;
            osdWrapper.osdMuted = false;
            osdWrapper.hasReceivedSocketMessage = false;
        }

        function test_parses_volume_message() {
            var result = osdWrapper.handleOsdMessage('{"type":"volume","value":75,"muted":false}');
            verify(result);
            compare(osdWrapper.osdType, "volume");
            compare(osdWrapper.osdValue, 75);
            compare(osdWrapper.osdMuted, false);
            verify(osdWrapper.hasReceivedSocketMessage);
        }

        function test_parses_brightness_message() {
            var result = osdWrapper.handleOsdMessage('{"type":"brightness","value":50,"muted":false}');
            verify(result);
            compare(osdWrapper.osdType, "brightness");
            compare(osdWrapper.osdValue, 50);
        }

        function test_parses_mic_message_muted() {
            var result = osdWrapper.handleOsdMessage('{"type":"mic","value":100,"muted":true}');
            verify(result);
            compare(osdWrapper.osdType, "mic");
            compare(osdWrapper.osdMuted, true);
        }

        function test_defaults_type_to_volume_when_missing() {
            osdWrapper.handleOsdMessage('{"value":50}');
            compare(osdWrapper.osdType, "volume");
        }

        function test_defaults_value_to_zero_when_missing() {
            osdWrapper.handleOsdMessage('{"type":"volume"}');
            compare(osdWrapper.osdValue, 0);
        }

        function test_defaults_muted_to_false_when_missing() {
            osdWrapper.handleOsdMessage('{"type":"volume","value":50}');
            compare(osdWrapper.osdMuted, false);
        }

        function test_returns_false_for_invalid_json() {
            var result = osdWrapper.handleOsdMessage("not valid json");
            verify(!result);
            verify(!osdWrapper.hasReceivedSocketMessage);
        }

        function test_returns_false_for_empty_string() {
            var result = osdWrapper.handleOsdMessage("");
            verify(!result);
        }

        function test_handles_zero_value() {
            osdWrapper.handleOsdMessage('{"type":"volume","value":0,"muted":false}');
            compare(osdWrapper.osdValue, 0);
        }

        function test_handles_max_value() {
            osdWrapper.handleOsdMessage('{"type":"volume","value":100,"muted":false}');
            compare(osdWrapper.osdValue, 100);
        }

        function test_handles_over_100_value() {
            osdWrapper.handleOsdMessage('{"type":"volume","value":150,"muted":false}');
            compare(osdWrapper.osdValue, 150);
        }
    }

    TestCase {
        name: "OsdContentApplyValueFromMouseY"

        function test_top_of_track_gives_100() {
            compare(osdContent.applyValueFromMouseY(0, 120), 100);
        }

        function test_bottom_of_track_gives_0() {
            compare(osdContent.applyValueFromMouseY(120, 120), 0);
        }

        function test_middle_of_track_gives_50() {
            compare(osdContent.applyValueFromMouseY(60, 120), 50);
        }

        function test_negative_mouseY_clamped_to_100() {
            compare(osdContent.applyValueFromMouseY(-10, 120), 100);
        }

        function test_mouseY_beyond_track_clamped_to_0() {
            compare(osdContent.applyValueFromMouseY(200, 120), 0);
        }

        function test_quarter_position() {
            compare(osdContent.applyValueFromMouseY(30, 120), 75);
        }

        function test_three_quarter_position() {
            compare(osdContent.applyValueFromMouseY(90, 120), 25);
        }
    }

    TestCase {
        name: "OsdContentClampedFraction"

        function test_normal_value_within_range() {
            fuzzyCompare(osdContent.computeClampedFraction(50), 0.5, 0.001);
        }

        function test_zero_value() {
            fuzzyCompare(osdContent.computeClampedFraction(0), 0.0, 0.001);
        }

        function test_100_value() {
            fuzzyCompare(osdContent.computeClampedFraction(100), 1.0, 0.001);
        }

        function test_over_100_clamped_to_1() {
            fuzzyCompare(osdContent.computeClampedFraction(150), 1.0, 0.001);
        }

        function test_25_percent() {
            fuzzyCompare(osdContent.computeClampedFraction(25), 0.25, 0.001);
        }
    }

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

    TestCase {
        name: "OsdContentDisplayText"

        function test_shows_percentage_when_not_muted() {
            compare(osdContent.computeDisplayText(false, 75), "75%");
        }

        function test_shows_m_when_muted() {
            compare(osdContent.computeDisplayText(true, 75), "M");
        }

        function test_shows_zero_percent() {
            compare(osdContent.computeDisplayText(false, 0), "0%");
        }

        function test_shows_100_percent() {
            compare(osdContent.computeDisplayText(false, 100), "100%");
        }
    }

    TestCase {
        name: "OsdContentWheelDelta"

        function test_scroll_up_increases_by_5() {
            compare(osdContent.computeWheelNewValue(50, 120), 55);
        }

        function test_scroll_down_decreases_by_5() {
            compare(osdContent.computeWheelNewValue(50, -120), 45);
        }

        function test_scroll_up_clamped_at_100() {
            compare(osdContent.computeWheelNewValue(98, 120), 100);
        }

        function test_scroll_down_clamped_at_0() {
            compare(osdContent.computeWheelNewValue(3, -120), 0);
        }

        function test_scroll_up_from_0() {
            compare(osdContent.computeWheelNewValue(0, 120), 5);
        }

        function test_scroll_down_from_100() {
            compare(osdContent.computeWheelNewValue(100, -120), 95);
        }

        function test_scroll_up_at_100_stays_at_100() {
            compare(osdContent.computeWheelNewValue(100, 120), 100);
        }

        function test_scroll_down_at_0_stays_at_0() {
            compare(osdContent.computeWheelNewValue(0, -120), 0);
        }
    }
}
