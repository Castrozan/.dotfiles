import QtQuick
import QtTest

OnScreenDisplayFixture {
    id: root

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
}
