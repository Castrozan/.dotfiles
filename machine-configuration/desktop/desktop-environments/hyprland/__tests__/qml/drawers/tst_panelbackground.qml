import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/frame"

Item {
    width: 800
    height: 600

    Rectangle {
        id: desktop
        anchors.fill: parent
        color: "white"

        BarBackgroundShape {
            id: panelShape
            anchors.fill: parent
            fillColor: "#202020"
            strokeColor: "#c000ff"

            geometry: BarFrameGeometry {
                id: panelGeometry
                leftBarWidth: 0
                barHeight: desktop.height
                screenWidth: desktop.width
                junctionRadius: 24
                extensionY: 200
                extensionHeight: 200
                extensionWidth: 0
                dashboardX: 300
                dashboardWidth: 200
                dashboardHeight: 0
                launcherX: 300
                launcherWidth: 200
                launcherHeight: 0
                rightPanelY: 200
                rightPanelWidth: 0
                rightPanelHeight: 0
            }
        }
    }

    TestCase {
        name: "PanelBackgroundRendering"
        when: windowShown

        function init() {
            panelGeometry.leftBarWidth = 0;
            panelGeometry.extensionWidth = 0;
            panelGeometry.extensionY = 200;
            panelGeometry.extensionHeight = 200;
            panelGeometry.dashboardHeight = 0;
            panelGeometry.launcherHeight = 0;
            panelGeometry.rightPanelWidth = 0;
            panelGeometry.rightPanelY = 200;
            panelGeometry.rightPanelHeight = 0;
        }

        function renderedDesktop() {
            waitForRendering(panelShape);
            return grabImage(desktop);
        }

        function test_open_bar_does_not_darken_the_desktop_data() {
            return [
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

        function test_open_bar_does_not_darken_the_desktop(data) {
            panelGeometry.leftBarWidth = data.width;
            const image = renderedDesktop();
            for (const point of [Qt.point(400, 300), Qt.point(400, 1), Qt.point(798, 300), Qt.point(400, 598)]) {
                compare(image.red(point.x, point.y), 255);
                compare(image.green(point.x, point.y), 255);
                compare(image.blue(point.x, point.y), 255);
            }
            compare(image.red(data.width / 2, 300), 32);
        }

        function test_open_panel_has_fill_and_outline_data() {
            return [
                {
                    tag: "dashboard",
                    property: "dashboardHeight",
                    value: 120,
                    x: 400,
                    y: 60,
                    borderX: 400,
                    borderY: 120
                },
                {
                    tag: "launcher",
                    property: "launcherHeight",
                    value: 120,
                    x: 400,
                    y: 550,
                    borderX: 400,
                    borderY: 479
                },
                {
                    tag: "right",
                    property: "rightPanelWidth",
                    value: 80,
                    x: 760,
                    y: 300,
                    borderX: 719,
                    borderY: 300
                },
                {
                    tag: "popout",
                    property: "extensionWidth",
                    value: 200,
                    x: 100,
                    y: 300,
                    borderX: 248,
                    borderY: 300
                }
            ];
        }

        function test_open_panel_has_fill_and_outline(data) {
            panelGeometry.leftBarWidth = data.tag === "popout" ? 48 : 0;
            panelGeometry.rightPanelHeight = data.tag === "right" ? 200 : 0;
            panelGeometry[data.property] = data.value;
            const image = renderedDesktop();
            compare(image.red(data.x, data.y), 32);
            verify(Math.abs(image.red(data.borderX, data.borderY) - 192) <= 10);
            verify(image.green(data.borderX, data.borderY) <= 10);
            verify(image.blue(data.borderX, data.borderY) >= 240);
            compare(image.red(400, 300), 255);
        }

        function test_closed_panels_leave_the_desktop_unpainted() {
            const image = renderedDesktop();
            for (const point of [Qt.point(1, 1), Qt.point(1, 300), Qt.point(400, 1), Qt.point(798, 300), Qt.point(400, 598), Qt.point(400, 300)])
                compare(image.red(point.x, point.y), 255);
        }

        function test_popout_at_screen_edges_has_fill() {
            panelGeometry.leftBarWidth = 48;
            panelGeometry.extensionWidth = 200;
            for (const position of [0, 400]) {
                panelGeometry.extensionY = position;
                const image = renderedDesktop();
                compare(image.red(100, position + 100), 32);
                compare(image.red(400, 300), 255);
            }
        }

        function test_full_height_right_panel_has_fill() {
            panelGeometry.rightPanelWidth = 200;
            panelGeometry.rightPanelY = 0;
            panelGeometry.rightPanelHeight = 600;
            const image = renderedDesktop();
            compare(image.red(700, 300), 32);
            compare(image.red(400, 300), 255);
            verify(image.green(599, 300) <= 10);
        }

        function test_overlapping_panels_do_not_clear_each_other() {
            panelGeometry.rightPanelWidth = 400;
            panelGeometry.rightPanelY = 0;
            panelGeometry.rightPanelHeight = 200;
            panelGeometry.dashboardHeight = 200;
            const image = renderedDesktop();
            compare(image.red(450, 60), 32);
            compare(image.red(400, 300), 255);
        }

        function test_empty_popout_does_not_paint_a_stray_border() {
            panelGeometry.leftBarWidth = 48;
            panelGeometry.extensionWidth = 200;
            panelGeometry.extensionHeight = 0;
            compare(renderedDesktop().red(100, 200), 255);
        }
    }
}
