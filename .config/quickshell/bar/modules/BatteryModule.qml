import QtQuick
import QtQuick.Layouts
import Quickshell.Io
import ".."

ColumnLayout {
    id: batteryModuleRoot

    spacing: 0

    property int batteryCapacity: 0
    property string batteryStatus: "Unknown"
    property var screenScope: null
    property bool hovering: false

    Timer {
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            batteryCapacityProcess.running = true;
            batteryStatusProcess.running = true;
        }
    }

    Process {
        id: batteryCapacityProcess
        command: ["cat", "/sys/class/power_supply/BAT0/capacity"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                batteryModuleRoot.batteryCapacity = parseInt(data.trim()) || 0;
            }
        }
    }

    Process {
        id: batteryStatusProcess
        command: ["cat", "/sys/class/power_supply/BAT0/status"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                batteryModuleRoot.batteryStatus = data.trim();
            }
        }
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: {
            if (batteryModuleRoot.batteryStatus === "Charging") return "⚡";
            if (batteryModuleRoot.batteryStatus === "Discharging") return "🔋";
            return "󰀞";
        }
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: {
            if (batteryModuleRoot.batteryCapacity <= 20 && batteryModuleRoot.batteryStatus !== "Charging")
                return ThemeColors.warning;
            return ThemeColors.foreground;
        }

        Behavior on color {
            ColorAnimation { duration: 150 }
        }
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: batteryModuleRoot.batteryCapacity + "%"
        font.pixelSize: 16
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: {
            if (batteryModuleRoot.batteryCapacity <= 20 && batteryModuleRoot.batteryStatus !== "Charging")
                return ThemeColors.warning;
            return ThemeColors.foreground;
        }

        Behavior on color {
            ColorAnimation { duration: 150 }
        }
    }

    MouseArea {
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredHeight: 40
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: {
            if (batteryModuleRoot.screenScope) {
                batteryModuleRoot.screenScope.togglePopout("battery");
            }
        }

        onContainsMouseChanged: {
            batteryModuleRoot.hovering = containsMouse;
        }
    }
}
