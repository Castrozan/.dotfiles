pragma ComponentBehavior: Bound

import Quickshell.Io
import "../dashboard/components"
import "../dashboard"
import QtQuick
import QtQuick.Layouts

Item {
    id: sessionContentRoot

    implicitWidth: sessionButtonsColumn.implicitWidth + Appearance.padding.large * 2
    implicitHeight: sessionButtonsColumn.implicitHeight + Appearance.padding.large * 2

    ColumnLayout {
        id: sessionButtonsColumn

        anchors.centerIn: parent
        spacing: Appearance.spacing.small

        SessionActionButton {
            iconName: "fullscreen"
            command: ["hyprctl", "dispatch", "fullscreen", "0"]
        }

        SessionActionButton {
            iconName: "lock"
            command: ["loginctl", "lock-session"]
        }

        SessionActionButton {
            iconName: "logout"
            command: ["hyprctl", "dispatch", "exit"]
        }

        SessionActionButton {
            iconName: "dark_mode"
            command: ["systemctl", "suspend"]
        }

        SessionActionButton {
            iconName: "restart_alt"
            command: ["systemctl", "reboot"]
        }

        SessionActionButton {
            iconName: "power_settings_new"
            activeColour: Colours.palette.m3error
            activeOnColour: Colours.palette.m3onPrimary
            command: ["systemctl", "poweroff"]
        }
    }

    component SessionActionButton: IconButton {
        id: sessionActionButtonRoot

        required property var command
        property string iconName

        Layout.alignment: Qt.AlignHCenter

        icon: iconName
        type: IconButton.Tonal

        implicitWidth: 48
        implicitHeight: 48

        font.pointSize: Appearance.font.size.extraLarge

        Process {
            id: sessionActionProcess
            command: sessionActionButtonRoot.command
            running: false
        }

        onClicked: sessionActionProcess.running = true
    }
}
