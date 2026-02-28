import Quickshell.Hyprland
import QtQuick
import QtQuick.Layouts
import "modules" as Modules

ColumnLayout {
    id: barRoot

    required property var screenScope

    spacing: 2

    readonly property bool hasHoveredPopoutIcon: mprisHoverZone.isHovered || statusIconsModule.hasHoveredPopoutIcon
    property var statusIconPositions: ({})

    function checkPopout(mouseY: real): void {
        let localY = mapFromItem(parent, 0, mouseY).y;

        for (let iconName in statusIconPositions) {
            let pos = statusIconPositions[iconName];
            if (localY >= pos.top && localY <= pos.bottom) {
                if (iconName !== "") {
                    screenScope.showPopout(iconName, mouseY);
                }
                return;
            }
        }
    }

    function handleWheel(mouseY: real, angleDelta: point): void {
        let localY = mapFromItem(parent, 0, mouseY).y;
        let workspacesTop = workspacesModule.y;
        let workspacesBottom = workspacesModule.y + workspacesModule.height;

        if (localY >= workspacesTop && localY <= workspacesBottom) {
            if (angleDelta.y > 0) {
                Hyprland.dispatch("workspace m-1");
            } else if (angleDelta.y < 0) {
                Hyprland.dispatch("workspace m+1");
            }
        }
    }

    function registerStatusIconPosition(name: string, top: real, bottom: real): void {
        let positions = statusIconPositions;
        positions[name] = { top: top, bottom: bottom };
        statusIconPositions = positions;
    }

    Item {
        id: mprisHoverZone
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
        Layout.preferredHeight: 20

        readonly property bool isHovered: mprisHoverMouseArea.containsMouse

        MouseArea {
            id: mprisHoverMouseArea
            anchors.fill: parent
            hoverEnabled: true
            onContainsMouseChanged: {
                if (containsMouse) {
                    barRoot.screenScope.showPopout("mpris", barRoot.height / 3);
                }
            }
        }
    }

    Modules.LauncherButton {
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
        Layout.preferredHeight: 40
    }

    Modules.WorkspacesModule {
        id: workspacesModule
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
    }

    Item {
        Layout.fillHeight: true
    }

    Modules.TrayModule {
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
        screenScope: barRoot.screenScope
    }

    Modules.ClockModule {
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
    }

    Modules.StatusIconsModule {
        id: statusIconsModule
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40

        barRoot: barRoot
        screenScope: barRoot.screenScope
    }

    Modules.PowerButton {
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 40
        Layout.preferredHeight: 40
        Layout.bottomMargin: 4
    }
}
