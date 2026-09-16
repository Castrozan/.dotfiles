import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIconsPopoutRow {
    id: bluetoothRowRoot

    required property bool active

    property bool bluetoothPowered: true
    property bool bluetoothHasConnectedDevices: false

    onActiveChanged: {
        if (active) {
            bluetoothPoweredProcess.running = true;
            bluetoothConnectedProcess.running = true;
        }
    }

    Process {
        id: bluetoothLauncherProcess
        command: ["hyprctl", "dispatch", "exec", "wezterm start -- bluetui"]
        running: false
    }

    Process {
        id: bluetoothPoweredProcess
        command: ["bluetoothctl", "show"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                bluetoothRowRoot.bluetoothPowered = data.indexOf("Powered: yes") !== -1;
            }
        }
    }

    Process {
        id: bluetoothConnectedProcess
        command: ["bluetoothctl", "devices", "Connected"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                bluetoothRowRoot.bluetoothHasConnectedDevices = data.trim().length > 0;
            }
        }
    }

    rowIconText: {
        if (!bluetoothRowRoot.bluetoothPowered)
            return "󰂲";
        if (bluetoothRowRoot.bluetoothHasConnectedDevices)
            return "󰂱";
        return "󰂯";
    }
    rowLabel: "Bluetooth"
    rowStateText: {
        if (!bluetoothRowRoot.bluetoothPowered)
            return "off";
        if (bluetoothRowRoot.bluetoothHasConnectedDevices)
            return "connected";
        return "on";
    }
    onRowClicked: bluetoothLauncherProcess.running = true
}
