import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/frame"

Item {
    BarFrameGeometry {
        id: geometry
        barWidth: 48
        leftBarWidth: 16
        barHeight: 1080
        screenWidth: 1920
        junctionRadius: 36
        extensionY: 500
        extensionHeight: 200
        extensionWidth: 0
        dashboardX: 568
        dashboardWidth: 832
        dashboardHeight: 0
        launcherX: 708
        launcherWidth: 552
        launcherHeight: 0
        rightPanelY: 16
        rightPanelWidth: 0
        rightPanelHeight: 0
    }

    PopoutContour {
        id: contour
        geometry: geometry
    }

    TestCase {
        name: "BarFrameAutoHideGeometry"

        function init() {
            geometry.leftBarWidth = 16;
            geometry.extensionWidth = 0;
            geometry.extensionY = 500;
        }

        function test_reveal_keeps_frame_edges_fixed_data() {
            return [
                {
                    tag: "hidden",
                    width: 16
                },
                {
                    tag: "animating",
                    width: 32
                },
                {
                    tag: "shown",
                    width: 48
                }
            ];
        }

        function test_reveal_keeps_frame_edges_fixed(data) {
            geometry.leftBarWidth = data.width;
            compare(geometry.stripThickness, 16);
            compare(geometry.rightStripLeftEdge, 1904);
            compare(geometry.topEdgeTargetX, data.width + 16);
            compare(geometry.bottomEdgeTargetX, data.width + 16);
        }

        function test_popout_remains_attached_during_reveal_data() {
            return [
                {
                    tag: "hidden",
                    width: 16
                },
                {
                    tag: "animating",
                    width: 32
                },
                {
                    tag: "shown",
                    width: 48
                }
            ];
        }

        function test_popout_remains_attached_during_reveal(data) {
            geometry.leftBarWidth = data.width;
            geometry.extensionWidth = 312;
            compare(geometry.extensionRight, data.width + 312);
            compare(geometry.stripThickness, 16);
            compare(geometry.extensionTopEdge, 500);
            compare(geometry.extensionBottomEdge, 700);
        }

        function test_empty_popout_stays_between_corner_tangents_data() {
            return test_reveal_keeps_frame_edges_fixed_data();
        }

        function test_empty_popout_stays_between_corner_tangents(data) {
            geometry.leftBarWidth = data.width;
            for (const position of [16, 500, 1064]) {
                geometry.extensionY = position;
                for (const element of contour.elements) {
                    if (element.x === geometry.leftBarWidth) {
                        verify(element.y >= geometry.barRightEdgeStartY, "Empty popout crosses the top corner tangent");
                        verify(element.y <= geometry.barRightEdgeEndY, "Empty popout crosses the bottom corner tangent");
                    }
                }
            }
        }
    }
}
