import Quickshell.Io
import Quickshell.Bluetooth
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: bluetoothIcon

    popoutName: "bluetooth"

    readonly property bool isPowered: Bluetooth.defaultAdapter?.enabled ?? false
    readonly property bool hasConnectedDevices: Bluetooth.defaultAdapter?.devices.values.some(device => device.connected) ?? false

    iconText: {
        if (!isPowered)
            return "󰂲";
        if (hasConnectedDevices)
            return "󰂱";
        return "󰂯";
    }
    iconColor: ThemeColors.foreground

    onClicked: launchBluetoothProcess.running = true

    Process {
        id: launchBluetoothProcess
        command: ["hyprctl", "dispatch", "exec", "wezterm start -- bluetui"]
        running: false
    }
}
