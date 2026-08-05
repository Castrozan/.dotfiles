import Quickshell.Io
import QtQuick
import ".."

Rectangle {
    id: powerButtonRoot

    radius: 8
    color: powerButtonMouseArea.containsMouse ? ThemeColors.surfaceTranslucent : "transparent"

    Text {
        anchors.centerIn: parent
        text: "⏻"
        font.pixelSize: 16
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.error
    }

    MouseArea {
        id: powerButtonMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: launchWlogoutProcess.running = true
    }

    Process {
        id: launchWlogoutProcess
        command: ["wlogout"]
        running: false
    }
}
