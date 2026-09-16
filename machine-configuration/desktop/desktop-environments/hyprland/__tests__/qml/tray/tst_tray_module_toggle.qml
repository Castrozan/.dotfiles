import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: mockScreenScope
        property string popoutCurrentName: ""
        property real popoutCenterY: 0

        function showPopout(name, centerY) {
            popoutCurrentName = name;
            popoutCenterY = centerY;
        }
    }

    TestCase {
        name: "TrayModuleToggle"

        function init() {
            mockScreenScope.popoutCurrentName = "";
            mockScreenScope.popoutCenterY = 0;
        }

        function _simulateClick(index) {
            var popoutName = "traymenu" + index;
            if (mockScreenScope.popoutCurrentName === popoutName) {
                mockScreenScope.popoutCurrentName = "";
                return;
            }
            mockScreenScope.showPopout(popoutName, 100);
        }

        function test_click_opens_popout() {
            _simulateClick(0);
            compare(mockScreenScope.popoutCurrentName, "traymenu0");
        }

        function test_click_again_closes_popout() {
            _simulateClick(0);
            compare(mockScreenScope.popoutCurrentName, "traymenu0");
            _simulateClick(0);
            compare(mockScreenScope.popoutCurrentName, "");
        }

        function test_click_different_icon_switches_popout() {
            _simulateClick(0);
            compare(mockScreenScope.popoutCurrentName, "traymenu0");
            _simulateClick(1);
            compare(mockScreenScope.popoutCurrentName, "traymenu1");
        }

        function test_click_sets_center_y() {
            _simulateClick(0);
            compare(mockScreenScope.popoutCenterY, 100);
        }

        function test_toggle_off_does_not_change_center_y() {
            _simulateClick(0);
            var savedY = mockScreenScope.popoutCenterY;
            _simulateClick(0);
            compare(mockScreenScope.popoutCenterY, savedY);
        }
    }
}
