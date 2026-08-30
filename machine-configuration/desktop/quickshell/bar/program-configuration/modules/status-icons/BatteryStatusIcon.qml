import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: batteryIcon
    visible: MachineFeatures.hasBattery

    popoutName: "battery"

    property int batteryCapacity: 100
    property string batteryStatus: "Full"

    readonly property var chargingIcons: ["󰢜", "󰂆", "󰂇", "󰂈", "󰢝", "󰂉", "󰢞", "󰂊", "󰂋", "󰂅"]
    readonly property var dischargingIcons: ["󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]

    iconText: {
        if (batteryStatus === "Full") return "󰂅";
        let tier = Math.min(Math.floor(batteryCapacity / 11), 9);
        if (batteryStatus === "Charging") return chargingIcons[tier];
        return dischargingIcons[tier];
    }
    iconColor: {
        if (batteryCapacity <= 20 && batteryStatus !== "Charging") return ThemeColors.warning;
        return ThemeColors.foreground;
    }

    FileView {
        id: batteryCapacityFileView
        path: MachineFeatures.batteryPath !== "" ? MachineFeatures.batteryPath + "/capacity" : ""
        onLoaded: {
            batteryIcon.batteryCapacity = parseInt(text().trim()) || 0;
        }
    }

    FileView {
        id: batteryStatusFileView
        path: MachineFeatures.batteryPath !== "" ? MachineFeatures.batteryPath + "/status" : ""
        onLoaded: {
            batteryIcon.batteryStatus = text().trim();
        }
    }

    Timer {
        interval: 30000
        running: MachineFeatures.hasBattery
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            batteryCapacityFileView.reload();
            batteryStatusFileView.reload();
        }
    }
}
