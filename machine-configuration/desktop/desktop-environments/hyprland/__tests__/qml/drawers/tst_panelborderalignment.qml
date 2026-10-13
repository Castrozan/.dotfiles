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
            color: "#00ff00"
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
        name: "PanelBorderAlignment"
        when: windowShown

        function init() {
            panelGeometry.leftBarWidth = 0;
            panelGeometry.extensionY = 200;
            panelGeometry.extensionWidth = 0;
            panelGeometry.dashboardHeight = 0;
            panelGeometry.launcherHeight = 0;
            panelGeometry.rightPanelY = 200;
            panelGeometry.rightPanelWidth = 0;
            panelGeometry.rightPanelHeight = 0;
        }

        function test_native_border_stays_within_corner_stroke_data() {
            return [
                {
                    tag: "left_top",
                    settings: {
                        leftBarWidth: 48
                    },
                    position: Qt.point(70, 1)
                },
                {
                    tag: "left_bottom",
                    settings: {
                        leftBarWidth: 48
                    },
                    position: Qt.point(70, 598)
                },
                {
                    tag: "right_top",
                    settings: {
                        rightPanelWidth: 80,
                        rightPanelHeight: 600,
                        rightPanelY: 0
                    },
                    position: Qt.point(698, 1)
                },
                {
                    tag: "right_bottom",
                    settings: {
                        rightPanelWidth: 80,
                        rightPanelHeight: 600,
                        rightPanelY: 0
                    },
                    position: Qt.point(698, 598)
                },
                {
                    tag: "popout_top",
                    settings: {
                        leftBarWidth: 48,
                        extensionWidth: 200,
                        extensionY: 0
                    },
                    position: Qt.point(270, 1)
                },
                {
                    tag: "popout_bottom",
                    settings: {
                        leftBarWidth: 48,
                        extensionWidth: 200,
                        extensionY: 400
                    },
                    position: Qt.point(270, 598)
                },
                {
                    tag: "dashboard",
                    settings: {
                        dashboardHeight: 120
                    },
                    position: Qt.point(278, 1)
                },
                {
                    tag: "launcher",
                    settings: {
                        launcherHeight: 120
                    },
                    position: Qt.point(278, 598)
                },
                {
                    tag: "right_junction_top",
                    settings: {
                        rightPanelWidth: 80,
                        rightPanelHeight: 200
                    },
                    position: Qt.point(798, 178)
                },
                {
                    tag: "right_junction_bottom",
                    settings: {
                        rightPanelWidth: 80,
                        rightPanelHeight: 200
                    },
                    position: Qt.point(798, 421)
                }
            ];
        }

        function test_native_border_stays_within_corner_stroke(data) {
            for (const [propertyName, value] of Object.entries(data.settings))
                panelGeometry[propertyName] = value;
            waitForRendering(panelShape);
            const image = grabImage(desktop);
            verify(image.green(data.position.x, data.position.y) < 40);
            verify(image.blue(data.position.x, data.position.y) > 100);
        }
    }
}
