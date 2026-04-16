import QtQuick
import QtQuick.Layouts
import Quickshell.Io
import ".."

ColumnLayout {
    id: batteryModuleRoot

    spacing: 0

    property int batteryCapacity: 100
    property string batteryStatus: "Full"

    readonly property var chargingIcons: ["󰢜", "󰂆", "󰂇", "󰂈", "󰢝", "󰂉", "󰢞", "󰂊", "󰂋", "󰂅"]
    readonly property var dischargingIcons: ["󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]

    readonly property string batteryIcon: {
        if (batteryStatus === "Full") return "󰂅";
        let tier = Math.min(Math.floor(batteryCapacity / 11), 9);
        if (batteryStatus === "Charging") return chargingIcons[tier];
        return dischargingIcons[tier];
    }

    readonly property color batteryColor: {
        if (batteryCapacity <= 10 && batteryStatus !== "Charging") return ThemeColors.error;
        if (batteryCapacity <= 20 && batteryStatus !== "Charging") return ThemeColors.warning;
        return ThemeColors.foreground;
    }

    Timer {
        interval: 30000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            batteryCapacityFileView.reload();
            batteryStatusFileView.reload();
        }
    }

    FileView {
        id: batteryCapacityFileView
        path: "/sys/class/power_supply/BAT0/capacity"
        onLoaded: {
            batteryModuleRoot.batteryCapacity = parseInt(text().trim()) || 0;
        }
    }

    FileView {
        id: batteryStatusFileView
        path: "/sys/class/power_supply/BAT0/status"
        onLoaded: {
            batteryModuleRoot.batteryStatus = text().trim();
        }
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: batteryModuleRoot.batteryIcon
        font.pixelSize: 18
        font.family: "JetBrainsMono Nerd Font"
        color: batteryModuleRoot.batteryColor
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: batteryModuleRoot.batteryCapacity + "%"
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: batteryModuleRoot.batteryColor
    }
}
