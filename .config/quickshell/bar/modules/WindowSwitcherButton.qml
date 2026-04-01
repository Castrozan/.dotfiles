import Quickshell.Io
import QtQuick
import ".."

Rectangle {
    id: windowSwitcherButtonRoot

    radius: 8
    color: windowSwitcherMouseArea.containsMouse ? ThemeColors.surfaceTranslucent : "transparent"

    Text {
        anchors.centerIn: parent
        text: "󰖯"
        font.pixelSize: 22
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    MouseArea {
        id: windowSwitcherMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: openWindowSwitcherProcess.running = true
    }

    Process {
        id: openWindowSwitcherProcess
        command: ["qs", "-c", "switcher", "ipc", "call", "switcher", "open"]
        running: false
    }
}
