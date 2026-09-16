import QtQuick
import QtTest

OnScreenDisplayFixture {
    id: root

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
