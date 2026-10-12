import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/frame"

Rectangle {
    id: desktop
    width: 800
    height: 600
    color: "white"

    Repeater {
        model: [Qt.rect(0, 0, 800, 2), Qt.rect(0, 598, 800, 2), Qt.rect(0, 0, 2, 600), Qt.rect(798, 0, 2, 600)]
        Rectangle {
            required property rect modelData
            x: modelData.x
            y: modelData.y
            width: modelData.width
            height: modelData.height
            color: "#c000ff"
        }
    }

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

    TestCase {
        name: "PanelWindowJunctionRendering"
        when: windowShown

        function init() {
            panelGeometry.leftBarWidth = 0;
            panelGeometry.extensionWidth = 0;
            panelGeometry.extensionY = 200;
            panelGeometry.extensionHeight = 200;
            panelGeometry.dashboardHeight = 0;
            panelGeometry.launcherHeight = 0;
            panelGeometry.rightPanelWidth = 0;
            panelGeometry.rightPanelHeight = 0;
            panelGeometry.rightPanelY = 200;
        }

        function test_attachment_replaces_the_window_border_data() {
            return [
                {
                    tag: "top",
                    property: "dashboardHeight",
                    value: 120,
                    attached: Qt.point(400, 0),
                    outside: Qt.point(100, 0)
                },
                {
                    tag: "bottom",
                    property: "launcherHeight",
                    value: 120,
                    attached: Qt.point(400, 599),
                    outside: Qt.point(100, 599)
                },
                {
                    tag: "right",
                    property: "rightPanelWidth",
                    value: 80,
                    attached: Qt.point(799, 300),
                    outside: Qt.point(799, 100)
                },
                {
                    tag: "right_full_top",
                    property: "rightPanelWidth",
                    value: 80,
                    attached: Qt.point(760, 0),
                    outside: Qt.point(100, 0)
                },
                {
                    tag: "right_full_bottom",
                    property: "rightPanelWidth",
                    value: 80,
                    attached: Qt.point(760, 599),
                    outside: Qt.point(100, 599)
                },
                {
                    tag: "left",
                    property: "leftBarWidth",
                    value: 48,
                    attached: Qt.point(0, 300),
                    outside: Qt.point(799, 300)
                }
            ];
        }

        function test_attachment_replaces_the_window_border(data) {
            const fullHeight = data.tag.startsWith("right_full");
            panelGeometry.rightPanelY = fullHeight ? 0 : 200;
            panelGeometry.rightPanelHeight = data.property === "rightPanelWidth" ? (fullHeight ? 600 : 200) : 0;
            panelGeometry[data.property] = data.value;
            waitForRendering(panelShape);
            const image = grabImage(desktop);
            compare(image.red(data.attached.x, data.attached.y), 32);
            compare(image.green(data.attached.x, data.attached.y), 32);
            compare(image.blue(data.attached.x, data.attached.y), 32);
            compare(image.red(data.outside.x, data.outside.y), 192);
            compare(image.blue(data.outside.x, data.outside.y), 255);
            compare(image.red(400, 300), 255);
        }

        function test_top_junction_preserves_the_concave_curve() {
            panelGeometry.dashboardHeight = 120;
            waitForRendering(panelShape);
            const image = grabImage(desktop);
            compare(image.red(276, 3), 255);
            compare(image.red(300, 3), 32);
            verify(image.red(292, 7) > 80);
            verify(image.green(292, 7) < 50);
            verify(image.blue(292, 7) > 100);
            verify(image.green(300, 60) < 10);
            verify(image.blue(400, 119) > 240);
        }

        function test_full_height_panel_preserves_window_corners() {
            panelGeometry.rightPanelWidth = 80;
            panelGeometry.rightPanelHeight = 600;
            panelGeometry.rightPanelY = 0;
            waitForRendering(panelShape);
            const image = grabImage(desktop);
            compare(image.red(720, 3), 32);
            verify(image.green(712, 7) < 50);
            verify(image.blue(712, 7) > 100);
            verify(image.green(712, 592) < 50);
            verify(image.blue(712, 592) > 100);
        }

        function test_left_bar_preserves_window_corners() {
            panelGeometry.leftBarWidth = 48;
            waitForRendering(panelShape);
            const image = grabImage(desktop);
            compare(image.red(48, 3), 32);
            verify(image.green(55, 7) < 50);
            verify(image.blue(55, 7) > 100);
            verify(image.green(55, 592) < 50);
            verify(image.blue(55, 592) > 100);
        }

        function test_edge_popout_preserves_window_corners() {
            panelGeometry.leftBarWidth = 48;
            panelGeometry.extensionWidth = 200;
            for (const position of [0, 400]) {
                panelGeometry.extensionY = position;
                waitForRendering(panelShape);
                const image = grabImage(desktop);
                const edgeY = position === 0 ? 3 : 597;
                const cornerY = position === 0 ? 7 : 592;
                compare(image.red(248, edgeY), 32);
                verify(image.green(255, cornerY) < 50);
                verify(image.blue(255, cornerY) > 100);
            }
        }

        function test_near_edge_popout_preserves_window_corners() {
            panelGeometry.leftBarWidth = 48;
            panelGeometry.extensionWidth = 200;
            panelGeometry.extensionHeight = 170;
            for (const position of [30, 400]) {
                panelGeometry.extensionY = position;
                waitForRendering(panelShape);
                const image = grabImage(desktop);
                compare(image.red(48, position === 30 ? 3 : 597), 32);
                verify(image.green(52, position === 30 ? 4 : 595) < 50);
                verify(image.blue(52, position === 30 ? 4 : 595) > 100);
            }
        }
    }
}
