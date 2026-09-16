import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIconsPopoutRow {
    id: networkRowRoot

    required property bool active

    property int networkSignalStrength: 0
    property string networkConnectionState: "disconnected"
    property string networkCurrentSsid: ""
    readonly property var wifiSignalIcons: ["󰤯", "󰤟", "󰤢", "󰤥", "󰤨"]

    onActiveChanged: {
        if (active) {
            networkDeviceStatusProcess.running = true;
            networkSignalStrengthProcess.running = true;
        }
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
                    if (parts.length < 3)
                        continue;
                    let deviceType = parts[0];
                    let deviceState = parts[1];
                    let connectionName = parts[2];

                    if (deviceType === "ethernet" && deviceState === "connected") {
                        networkRowRoot.networkConnectionState = "ethernet";
                        networkRowRoot.networkCurrentSsid = connectionName;
                        return;
                    }
                    if (deviceType === "wifi" && deviceState === "connected") {
                        networkRowRoot.networkConnectionState = "wifi";
                        foundWifi = true;
                        foundConnectionName = connectionName;
                    }
                }
                if (foundWifi) {
                    networkRowRoot.networkCurrentSsid = foundConnectionName;
                } else if (networkRowRoot.networkConnectionState !== "ethernet") {
                    networkRowRoot.networkConnectionState = "disconnected";
                    networkRowRoot.networkCurrentSsid = "";
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
                        networkRowRoot.networkSignalStrength = parseInt(parts[0]) || 0;
                        return;
                    }
                }
            }
        }
    }

    rowIconText: {
        if (networkRowRoot.networkConnectionState === "ethernet")
            return "󰀂";
        if (networkRowRoot.networkConnectionState === "disconnected")
            return "󰤮";
        let tier = Math.min(Math.floor(networkRowRoot.networkSignalStrength / 25), 4);
        return networkRowRoot.wifiSignalIcons[tier];
    }
    rowLabel: "Network"
    rowStateText: {
        if (networkRowRoot.networkConnectionState === "disconnected")
            return "off";
        return networkRowRoot.networkCurrentSsid;
    }
    onRowClicked: networkLauncherProcess.running = true
}
