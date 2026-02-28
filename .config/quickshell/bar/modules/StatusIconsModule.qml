import Quickshell
import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: statusIconsModuleRoot

    required property var barRoot
    required property var screenScope

    readonly property bool hasHoveredPopoutIcon: networkIcon.isHovered || bluetoothIcon.isHovered || batteryIcon.isHovered

    spacing: 2

    Component.onCompleted: _registerAllIconPositions()
    onYChanged: _registerAllIconPositions()
    onHeightChanged: _registerAllIconPositions()

    function _registerAllIconPositions(): void {
        _registerIconPosition(notificationSoundIcon, "");
        _registerIconPosition(microphoneIcon, "");
        _registerIconPosition(networkIcon, "network");
        _registerIconPosition(bluetoothIcon, "bluetooth");
        _registerIconPosition(batteryIcon, "battery");
    }

    function _registerIconPosition(iconItem: var, popoutName: string): void {
        if (!barRoot || !iconItem) return;
        let globalPos = iconItem.mapToItem(barRoot, 0, 0);
        barRoot.registerStatusIconPosition(popoutName, globalPos.y, globalPos.y + iconItem.height);
    }

    StatusIcon {
        id: notificationSoundIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        Layout.topMargin: 4

        property bool isMuted: false

        iconText: isMuted ? "󰂛" : "󰂚"
        iconColor: isMuted ? ThemeColors.warning : ThemeColors.foreground

        onClicked: notificationSoundToggleProcess.running = true

        Process {
            id: notificationSoundStatusProcess
            command: ["hypr-notification-sound-toggle", "status"]
            running: false
            stdout: SplitParser {
                splitMarker: ""
                onRead: data => {
                    try {
                        let parsed = JSON.parse(data);
                        notificationSoundIcon.isMuted = parsed.class === "muted";
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

        Timer {
            interval: 3000
            running: true
            repeat: true
            triggeredOnStart: true
            onTriggered: notificationSoundStatusProcess.running = true
        }
    }

    StatusIcon {
        id: microphoneIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28

        property bool isMuted: false

        iconText: isMuted ? "󰖁" : "󰍰"
        iconColor: isMuted ? ThemeColors.warning : ThemeColors.foreground

        onClicked: microphoneToggleProcess.running = true

        Process {
            id: microphoneStatusProcess
            command: ["hypr-microphone-toggle", "status"]
            running: false
            stdout: SplitParser {
                splitMarker: ""
                onRead: data => {
                    try {
                        let parsed = JSON.parse(data);
                        microphoneIcon.isMuted = parsed.class === "muted";
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

        Timer {
            interval: 3000
            running: true
            repeat: true
            triggeredOnStart: true
            onTriggered: microphoneStatusProcess.running = true
        }
    }

    StatusIcon {
        id: networkIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        popoutName: "network"
        screenScope: statusIconsModuleRoot.screenScope

        property int signalStrength: 0
        property string connectionState: "disconnected"

        readonly property var wifiSignalIcons: ["󰤯", "󰤟", "󰤢", "󰤥", "󰤨"]

        iconText: {
            if (connectionState === "ethernet") return "󰀂";
            if (connectionState === "disconnected") return "󰤮";
            let tier = Math.min(Math.floor(signalStrength / 25), 4);
            return wifiSignalIcons[tier];
        }
        iconColor: ThemeColors.foreground

        onClicked: launchNetworkProcess.running = true

        Process {
            id: launchNetworkProcess
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
                    for (let i = 0; i < lines.length; i++) {
                        let parts = lines[i].split(":");
                        if (parts.length < 3) continue;
                        let deviceType = parts[0];
                        let deviceState = parts[1];

                        if (deviceType === "ethernet" && deviceState === "connected") {
                            networkIcon.connectionState = "ethernet";
                            return;
                        }
                        if (deviceType === "wifi" && deviceState === "connected") {
                            networkIcon.connectionState = "wifi";
                            foundWifi = true;
                        }
                    }
                    if (!foundWifi && networkIcon.connectionState !== "ethernet") {
                        networkIcon.connectionState = "disconnected";
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
                            networkIcon.signalStrength = parseInt(parts[0]) || 0;
                            return;
                        }
                    }
                }
            }
        }

        Timer {
            interval: 5000
            running: true
            repeat: true
            triggeredOnStart: true
            onTriggered: {
                networkDeviceStatusProcess.running = true;
                networkSignalStrengthProcess.running = true;
            }
        }
    }

    StatusIcon {
        id: bluetoothIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        popoutName: "bluetooth"
        screenScope: statusIconsModuleRoot.screenScope

        property bool isPowered: true
        property bool hasConnectedDevices: false

        iconText: {
            if (!isPowered) return "󰂲";
            if (hasConnectedDevices) return "󰂱";
            return "";
        }
        iconColor: ThemeColors.foreground

        onClicked: launchBluetoothProcess.running = true

        Process {
            id: launchBluetoothProcess
            command: ["wezterm", "start", "--", "bluetui"]
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
            interval: 5000
            running: true
            repeat: true
            triggeredOnStart: true
            onTriggered: {
                bluetoothPoweredProcess.running = true;
                bluetoothConnectedProcess.running = true;
            }
        }
    }

    StatusIcon {
        id: batteryIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        popoutName: "battery"
        screenScope: statusIconsModuleRoot.screenScope

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

        Process {
            id: batteryCapacityProcess
            command: ["cat", "/sys/class/power_supply/BAT0/capacity"]
            running: false
            stdout: SplitParser {
                splitMarker: ""
                onRead: data => {
                    batteryIcon.batteryCapacity = parseInt(data.trim()) || 0;
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
                    batteryIcon.batteryStatus = data.trim();
                }
            }
        }

        Timer {
            interval: 5000
            running: true
            repeat: true
            triggeredOnStart: true
            onTriggered: {
                batteryCapacityProcess.running = true;
                batteryStatusProcess.running = true;
            }
        }
    }
}
