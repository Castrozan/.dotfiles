import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIconsPopoutRow {
    id: batteryRowRoot

    required property bool active

    property int batteryCapacity: 100
    property string batteryStatus: "Full"
    readonly property var batteryChargingIcons: ["󰢜", "󰂆", "󰂇", "󰂈", "󰢝", "󰂉", "󰢞", "󰂊", "󰂋", "󰂅"]
    readonly property var batteryDischargingIcons: ["󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]

    onActiveChanged: {
        if (active && MachineFeatures.hasBattery) {
            batteryCapacityFileView.reload();
            batteryStatusFileView.reload();
        }
    }

    FileView {
        id: batteryCapacityFileView
        path: MachineFeatures.batteryPath !== "" ? MachineFeatures.batteryPath + "/capacity" : ""
        onLoaded: {
            batteryRowRoot.batteryCapacity = parseInt(text().trim()) || 0;
        }
    }

    FileView {
        id: batteryStatusFileView
        path: MachineFeatures.batteryPath !== "" ? MachineFeatures.batteryPath + "/status" : ""
        onLoaded: {
            batteryRowRoot.batteryStatus = text().trim();
        }
    }

    visible: MachineFeatures.hasBattery
    rowIconText: {
        if (batteryRowRoot.batteryStatus === "Full")
            return "󰂅";
        let tier = Math.min(Math.floor(batteryRowRoot.batteryCapacity / 11), 9);
        if (batteryRowRoot.batteryStatus === "Charging")
            return batteryRowRoot.batteryChargingIcons[tier];
        return batteryRowRoot.batteryDischargingIcons[tier];
    }
    rowIconColor: {
        if (batteryRowRoot.batteryCapacity <= 20 && batteryRowRoot.batteryStatus !== "Charging")
            return ThemeColors.warning;
        return ThemeColors.foreground;
    }
    rowLabel: "Battery"
    rowStateText: batteryRowRoot.batteryCapacity + "%"
    rowStateColor: {
        if (batteryRowRoot.batteryCapacity <= 20 && batteryRowRoot.batteryStatus !== "Charging")
            return ThemeColors.warning;
        return ThemeColors.dim;
    }
}
