import QtQuick
import QtTest

Item {
    id: root

    Timer {
        id: mockPopoutHideTimer
        interval: 450
        property bool wasStopped: false

        function stop() {
            wasStopped = true;
            running = false;
        }

        function restart() {
            wasStopped = false;
            running = true;
        }
    }

    QtObject {
        id: mockDrawersScope
        property string popoutCurrentName: ""
        property real popoutCenterY: 0

        function showPopout(name, centerY) {
            mockPopoutHideTimer.stop();
            popoutCurrentName = name;
            popoutCenterY = centerY;
        }
    }

    TestCase {
        name: "ShowPopoutStopsHideTimer"

        function init() {
            mockDrawersScope.popoutCurrentName = "";
            mockDrawersScope.popoutCenterY = 0;
            mockPopoutHideTimer.wasStopped = false;
            mockPopoutHideTimer.running = false;
        }

        function test_showPopout_stops_pending_hide_timer() {
            mockPopoutHideTimer.restart();
            verify(mockPopoutHideTimer.running);

            mockDrawersScope.showPopout("traymenu0", 200);

            verify(mockPopoutHideTimer.wasStopped);
            verify(!mockPopoutHideTimer.running);
        }

        function test_showPopout_sets_name_and_position() {
            mockDrawersScope.showPopout("traymenu2", 350);
            compare(mockDrawersScope.popoutCurrentName, "traymenu2");
            compare(mockDrawersScope.popoutCenterY, 350);
        }

        function test_showPopout_stops_timer_even_when_not_running() {
            verify(!mockPopoutHideTimer.running);
            mockDrawersScope.showPopout("traymenu0", 100);
            verify(mockPopoutHideTimer.wasStopped);
        }
    }
}
