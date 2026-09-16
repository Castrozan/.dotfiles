import QtQuick
import QtTest

OnScreenDisplayFixture {
    id: root

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
}
