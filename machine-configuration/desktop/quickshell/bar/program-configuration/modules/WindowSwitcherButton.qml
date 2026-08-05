import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import QtQuick
import ".."

Rectangle {
    id: windowSwitcherButtonRoot

    readonly property string switcherSocketPath: Quickshell.env("XDG_RUNTIME_DIR") + "/quickshell-switcher.sock"

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

        onClicked: {
            Hyprland.dispatch("submap windowswitcher");
            sendSwitcherCommandProcess.running = true;
        }
    }

    Process {
        id: sendSwitcherCommandProcess
        command: ["sh", "-c", `printf 'open\n' | nc -U -N ${windowSwitcherButtonRoot.switcherSocketPath}`]
        running: false
    }
}
