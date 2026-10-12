import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/frame"

Item {
    BarFrameGeometry {
        id: geometry
        leftBarWidth: 0
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
            geometry.leftBarWidth = 0;
            geometry.extensionWidth = 0;
            geometry.extensionY = 500;
        }

        function test_reveal_keeps_frame_edges_fixed_data() {
            return [
                {
                    tag: "hidden",
                    width: 0,
                    outlineX: 0
                },
                {
                    tag: "animating",
                    width: 24,
                    outlineX: 48
                },
                {
                    tag: "shown",
                    width: 48,
                    outlineX: 84
                }
            ];
        }

        function test_reveal_keeps_frame_edges_fixed(data) {
            geometry.leftBarWidth = data.width;
            compare(geometry.stripThickness, 0);
            compare(geometry.rightStripLeftEdge, 1920);
            compare(geometry.topEdgeTargetX, data.outlineX);
            compare(geometry.bottomEdgeTargetX, data.outlineX);
        }

        function test_popout_remains_attached_during_reveal_data() {
            return [
                {
                    tag: "hidden",
                    width: 0
                },
                {
                    tag: "animating",
                    width: 24
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
            compare(geometry.stripThickness, 0);
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
