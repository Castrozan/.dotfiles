import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: statusIconsPopoutRoot

    property bool active: false

    property bool notificationSoundMuted: false
    property bool outputMuted: false
    property string outputDeviceType: "speaker"
    property bool microphoneMuted: false
    property int keyboardBacklightLevel: 2
    property int networkSignalStrength: 0
    property string networkConnectionState: "disconnected"
    property string networkCurrentSsid: ""
    property bool bluetoothPowered: true
    property bool bluetoothHasConnectedDevices: false
    property int batteryCapacity: 100
    property string batteryStatus: "Full"

    readonly property var keyboardBacklightLevels: [0, 5, 25, 50, 100]
    readonly property var keyboardBacklightIcons: ["󰌐", "󰌌", "󰌌", "󰌌", "󰌌"]
    readonly property var keyboardBacklightOpacities: [0.3, 0.4, 0.6, 0.8, 1.0]
    readonly property var wifiSignalIcons: ["󰤯", "󰤟", "󰤢", "󰤥", "󰤨"]
    readonly property var batteryChargingIcons: ["󰢜", "󰂆", "󰂇", "󰂈", "󰢝", "󰂉", "󰢞", "󰂊", "󰂋", "󰂅"]
    readonly property var batteryDischargingIcons: ["󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]

    spacing: 4

    onActiveChanged: {
        if (active) {
            notificationSoundStatusProcess.running = true;
            outputDefaultSinkProcess.running = true;
            outputMuteStatusProcess.running = true;
            microphoneStatusProcess.running = true;
            networkDeviceStatusProcess.running = true;
            networkSignalStrengthProcess.running = true;
            bluetoothPoweredProcess.running = true;
            bluetoothConnectedProcess.running = true;
            if (MachineFeatures.hasBattery) {
                batteryCapacityFileView.reload();
                batteryStatusFileView.reload();
            }
        }
    }

    Process {
        id: notificationSoundStatusProcess
        command: ["hypr-notification-sound-toggle", "status"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    let parsed = JSON.parse(data);
                    statusIconsPopoutRoot.notificationSoundMuted = parsed.class === "muted";
                } catch (e) {}
            }
        }
    }

    Process {
        id: notificationSoundToggleProcess
        command: ["hypr-notification-sound-toggle", "toggle"]
        running: false
        onExited: notificationSoundStatusProcess.running = true
    }

    Process {
        id: outputDefaultSinkProcess
        command: ["pactl", "get-default-sink"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const sinkName = data.trim();
                statusIconsPopoutRoot.outputDeviceType = sinkName.startsWith("bluez_") ? "bluetooth" : "speaker";
            }
        }
    }

    Process {
        id: outputMuteStatusProcess
        command: ["bash", "-c", "pactl get-default-sink | xargs pactl get-sink-mute"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                statusIconsPopoutRoot.outputMuted = data.trim() === "Mute: yes";
            }
        }
    }

    Process {
        id: outputMuteToggleProcess
        command: ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"]
        running: false
        onExited: {
            outputDefaultSinkProcess.running = true;
            outputMuteStatusProcess.running = true;
        }
    }

    Process {
        id: microphoneStatusProcess
        command: ["hypr-microphone-toggle", "status"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    let parsed = JSON.parse(data);
                    statusIconsPopoutRoot.microphoneMuted = parsed.class === "muted";
                } catch (e) {}
            }
        }
    }

    Process {
        id: microphoneToggleProcess
        command: ["hypr-microphone-toggle", "toggle"]
        running: false
        onExited: microphoneStatusProcess.running = true
    }

    Process {
        id: keyboardBacklightSetProcess
        command: ["set-keyboard-backlight-brightness", "5"]
        running: false
    }

    Process {
        id: networkLauncherProcess
        command: ["hypr-network"]
        running: false
    }

    Process {
        id: networkDeviceStatusProcess
        command: ["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device", "status"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                let lines = data.trim().split("\n");
                let foundWifi = false;
                let foundConnectionName = "";
                for (let i = 0; i < lines.length; i++) {
                    let parts = lines[i].split(":");
                    if (parts.length < 3) continue;
                    let deviceType = parts[0];
                    let deviceState = parts[1];
                    let connectionName = parts[2];

                    if (deviceType === "ethernet" && deviceState === "connected") {
                        statusIconsPopoutRoot.networkConnectionState = "ethernet";
                        statusIconsPopoutRoot.networkCurrentSsid = connectionName;
                        return;
                    }
                    if (deviceType === "wifi" && deviceState === "connected") {
                        statusIconsPopoutRoot.networkConnectionState = "wifi";
                        foundWifi = true;
                        foundConnectionName = connectionName;
                    }
                }
                if (foundWifi) {
                    statusIconsPopoutRoot.networkCurrentSsid = foundConnectionName;
                } else if (statusIconsPopoutRoot.networkConnectionState !== "ethernet") {
                    statusIconsPopoutRoot.networkConnectionState = "disconnected";
                    statusIconsPopoutRoot.networkCurrentSsid = "";
                }
            }
        }
    }

    Process {
        id: networkSignalStrengthProcess
        command: ["nmcli", "-t", "-f", "SIGNAL,IN-USE", "device", "wifi", "list"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                let lines = data.trim().split("\n");
                for (let i = 0; i < lines.length; i++) {
                    let parts = lines[i].split(":");
                    if (parts.length >= 2 && parts[1] === "*") {
                        statusIconsPopoutRoot.networkSignalStrength = parseInt(parts[0]) || 0;
                        return;
                    }
                }
            }
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
                statusIconsPopoutRoot.bluetoothPowered = data.indexOf("Powered: yes") !== -1;
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
                statusIconsPopoutRoot.bluetoothHasConnectedDevices = data.trim().length > 0;
            }
        }
    }

    FileView {
        id: batteryCapacityFileView
        path: MachineFeatures.batteryPath !== "" ? MachineFeatures.batteryPath + "/capacity" : ""
        onLoaded: {
            statusIconsPopoutRoot.batteryCapacity = parseInt(text().trim()) || 0;
        }
    }

    FileView {
        id: batteryStatusFileView
        path: MachineFeatures.batteryPath !== "" ? MachineFeatures.batteryPath + "/status" : ""
        onLoaded: {
            statusIconsPopoutRoot.batteryStatus = text().trim();
        }
    }

    StatusIconsPopoutRow {
        rowIconText: statusIconsPopoutRoot.notificationSoundMuted ? "󰂛" : "󰂚"
        rowIconColor: statusIconsPopoutRoot.notificationSoundMuted ? ThemeColors.warning : ThemeColors.foreground
        rowLabel: "Notifications"
        rowStateText: statusIconsPopoutRoot.notificationSoundMuted ? "muted" : ""
        onRowClicked: notificationSoundToggleProcess.running = true
    }

    StatusIconsPopoutRow {
        rowIconText: {
            if (statusIconsPopoutRoot.outputMuted) return "󰖁";
            if (statusIconsPopoutRoot.outputDeviceType === "bluetooth") return "󰋋";
            return "󰕾";
        }
        rowIconColor: statusIconsPopoutRoot.outputMuted ? ThemeColors.warning : ThemeColors.foreground
        rowLabel: "Sound"
        rowStateText: statusIconsPopoutRoot.outputMuted ? "muted" : ""
        onRowClicked: outputMuteToggleProcess.running = true
    }

    StatusIconsPopoutRow {
        rowIconText: statusIconsPopoutRoot.microphoneMuted ? "󰖁" : "󰍰"
        rowIconColor: statusIconsPopoutRoot.microphoneMuted ? ThemeColors.warning : ThemeColors.foreground
        rowLabel: "Microphone"
        rowStateText: statusIconsPopoutRoot.microphoneMuted ? "muted" : ""
        onRowClicked: microphoneToggleProcess.running = true
    }

    StatusIconsPopoutRow {
        visible: MachineFeatures.hasKeyboardBacklight
        rowIconText: statusIconsPopoutRoot.keyboardBacklightIcons[statusIconsPopoutRoot.keyboardBacklightLevel]
        rowIconColor: ThemeColors.foreground
        rowIconOpacity: statusIconsPopoutRoot.keyboardBacklightOpacities[statusIconsPopoutRoot.keyboardBacklightLevel]
        rowLabel: "Keyboard light"
        rowStateText: statusIconsPopoutRoot.keyboardBacklightLevels[statusIconsPopoutRoot.keyboardBacklightLevel] + "%"
        onRowClicked: {
            statusIconsPopoutRoot.keyboardBacklightLevel = (statusIconsPopoutRoot.keyboardBacklightLevel + 1) % statusIconsPopoutRoot.keyboardBacklightLevels.length;
            keyboardBacklightSetProcess.command = ["set-keyboard-backlight-brightness", String(statusIconsPopoutRoot.keyboardBacklightLevels[statusIconsPopoutRoot.keyboardBacklightLevel])];
            keyboardBacklightSetProcess.running = true;
        }
    }

    StatusIconsPopoutRow {
        rowIconText: {
            if (statusIconsPopoutRoot.networkConnectionState === "ethernet") return "󰀂";
            if (statusIconsPopoutRoot.networkConnectionState === "disconnected") return "󰤮";
            let tier = Math.min(Math.floor(statusIconsPopoutRoot.networkSignalStrength / 25), 4);
            return statusIconsPopoutRoot.wifiSignalIcons[tier];
        }
        rowLabel: "Network"
        rowStateText: {
            if (statusIconsPopoutRoot.networkConnectionState === "disconnected") return "off";
            return statusIconsPopoutRoot.networkCurrentSsid;
        }
        onRowClicked: networkLauncherProcess.running = true
    }

    StatusIconsPopoutRow {
        rowIconText: {
            if (!statusIconsPopoutRoot.bluetoothPowered) return "󰂲";
            if (statusIconsPopoutRoot.bluetoothHasConnectedDevices) return "󰂱";
            return "󰂯";
        }
        rowLabel: "Bluetooth"
        rowStateText: {
            if (!statusIconsPopoutRoot.bluetoothPowered) return "off";
            if (statusIconsPopoutRoot.bluetoothHasConnectedDevices) return "connected";
            return "on";
        }
        onRowClicked: bluetoothLauncherProcess.running = true
    }

    StatusIconsPopoutRow {
        visible: MachineFeatures.hasBattery
        rowIconText: {
            if (statusIconsPopoutRoot.batteryStatus === "Full") return "󰂅";
            let tier = Math.min(Math.floor(statusIconsPopoutRoot.batteryCapacity / 11), 9);
            if (statusIconsPopoutRoot.batteryStatus === "Charging") return statusIconsPopoutRoot.batteryChargingIcons[tier];
            return statusIconsPopoutRoot.batteryDischargingIcons[tier];
        }
        rowIconColor: {
            if (statusIconsPopoutRoot.batteryCapacity <= 20 && statusIconsPopoutRoot.batteryStatus !== "Charging") return ThemeColors.warning;
            return ThemeColors.foreground;
        }
        rowLabel: "Battery"
        rowStateText: statusIconsPopoutRoot.batteryCapacity + "%"
        rowStateColor: {
            if (statusIconsPopoutRoot.batteryCapacity <= 20 && statusIconsPopoutRoot.batteryStatus !== "Charging") return ThemeColors.warning;
            return ThemeColors.dim;
        }
    }
}
