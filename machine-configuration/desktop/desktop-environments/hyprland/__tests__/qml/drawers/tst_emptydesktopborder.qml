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
        name: "EmptyDesktopBorderRendering"
        when: windowShown

        function init() {
            panelShape.desktopBorderVisible = false;
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

        function test_empty_desktop_has_border_without_fill() {
            panelShape.desktopBorderVisible = true;
            const image = renderedDesktop();
            for (const position of [Qt.point(400, 1), Qt.point(798, 300), Qt.point(400, 598), Qt.point(1, 300)]) {
                verify(image.blue(position.x, position.y) > 100);
                verify(image.green(position.x, position.y) < 40);
            }
            compare(image.pixel(400, 300), desktop.color);
            compare(image.pixel(0, 0), desktop.color);
            panelShape.desktopBorderVisible = false;
            const occupiedImage = renderedDesktop();
            compare(occupiedImage.pixel(400, 1), desktop.color);
        }

        function test_empty_desktop_border_follows_panel_attachments() {
            panelShape.desktopBorderVisible = true;
            panelGeometry.leftBarWidth = 48;
            panelGeometry.dashboardHeight = 120;
            panelGeometry.launcherHeight = 120;
            panelGeometry.rightPanelWidth = 80;
            panelGeometry.rightPanelHeight = 200;
            const image = renderedDesktop();
            for (const position of [Qt.point(1, 300), Qt.point(400, 1), Qt.point(400, 598), Qt.point(798, 300)])
                compare(image.pixel(position.x, position.y), panelShape.fillColor);
            compare(image.pixel(600, 300), desktop.color);
            verify(image.blue(600, 1) > 100);
            verify(image.green(600, 1) < 40);
        }
    }
}
