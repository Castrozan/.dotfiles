import Quickshell.Io
import QtQuick
import ".."

Rectangle {
    id: launcherButtonRoot

    required property var screenScope

    radius: 8
    color: "transparent"

    Text {
        anchors.centerIn: parent
        text: "󱄅"
        font.pixelSize: 30
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.accent
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onClicked: mouse => {
            if (mouse.button === Qt.RightButton) {
                launchTerminalProcess.running = true;
            } else {
                launcherButtonRoot.screenScope.toggleLauncher();
            }
        }
    }

    Process {
        id: launchTerminalProcess
        command: ["wezterm"]
        running: false
    }
}
