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
            panelGeometry.dashboardHeight = 0;
            panelGeometry.launcherHeight = 0;
            panelGeometry.rightPanelWidth = 0;
            panelGeometry.rightPanelHeight = 0;
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
                    tag: "left",
                    property: "leftBarWidth",
                    value: 48,
                    attached: Qt.point(0, 300),
                    outside: Qt.point(799, 300)
                }
            ];
        }

        function test_attachment_replaces_the_window_border(data) {
            panelGeometry.rightPanelHeight = data.tag === "right" ? 200 : 0;
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
    }
}
