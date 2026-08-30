import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: bluetoothIcon

    popoutName: "bluetooth"

    property bool isPowered: true
    property bool hasConnectedDevices: false

    iconText: {
        if (!isPowered) return "󰂲";
        if (hasConnectedDevices) return "󰂱";
        return "󰂯";
    }
    iconColor: ThemeColors.foreground

    onClicked: launchBluetoothProcess.running = true

    Process {
        id: launchBluetoothProcess
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
                bluetoothIcon.isPowered = data.indexOf("Powered: yes") !== -1;
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
                bluetoothIcon.hasConnectedDevices = data.trim().length > 0;
            }
        }
    }

    Timer {
        interval: 30000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            bluetoothPoweredProcess.running = true;
            bluetoothConnectedProcess.running = true;
        }
    }
}
