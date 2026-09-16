import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: networkIcon

    popoutName: "network"

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
        interval: 30000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            networkDeviceStatusProcess.running = true;
            networkSignalStrengthProcess.running = true;
        }
    }
}
