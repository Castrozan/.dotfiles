import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: networkPopoutRoot

    property bool active: false

    property string currentSsid: ""
    property int currentSignal: 0
    property string currentIpAddress: ""
    property var availableNetworks: []

    spacing: 12

    onActiveChanged: {
        if (active) {
            fetchConnectionInfoProcess.running = true;
            fetchAvailableNetworksProcess.running = true;
        }
    }

    Process {
        id: fetchConnectionInfoProcess
        command: ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE,IP4.ADDRESS", "connection", "show", "--active"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                let lines = data.trim().split("\n");
                for (let i = 0; i < lines.length; i++) {
                    let parts = lines[i].split(":");
                    if (parts.length >= 3 && parts[1] === "802-11-wireless") {
                        networkPopoutRoot.currentSsid = parts[0];
                    }
                    if (lines[i].indexOf("IP4.ADDRESS") !== -1) {
                        let addressParts = lines[i].split(":");
                        if (addressParts.length >= 2) {
                            networkPopoutRoot.currentIpAddress = addressParts[addressParts.length - 1].split("/")[0];
                        }
                    }
                }
            }
        }
    }

    Process {
        id: fetchAvailableNetworksProcess
        command: ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "no"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                let lines = data.trim().split("\n");
                let networks = [];
                let seenSsids = {};
                for (let i = 0; i < lines.length; i++) {
                    let parts = lines[i].split(":");
                    if (parts.length < 2) continue;
                    let ssid = parts[0];
                    if (ssid === "" || seenSsids[ssid]) continue;
                    seenSsids[ssid] = true;
                    networks.push({
                        ssid: ssid,
                        signal: parseInt(parts[1]) || 0,
                        security: parts[2] || ""
                    });
                }
                networks.sort((a, b) => b.signal - a.signal);
                networkPopoutRoot.availableNetworks = networks.slice(0, 8);
            }
        }
    }

    Text {
        text: "Network"
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    ColumnLayout {
        spacing: 4
        visible: networkPopoutRoot.currentSsid !== ""

        Text {
            text: `Connected: ${networkPopoutRoot.currentSsid}`
            font.pixelSize: 12
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.accent
        }

        Text {
            text: networkPopoutRoot.currentIpAddress ? `IP: ${networkPopoutRoot.currentIpAddress}` : ""
            font.pixelSize: 11
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.dim
            visible: networkPopoutRoot.currentIpAddress !== ""
        }
    }

    Rectangle {
        Layout.fillWidth: true
        height: 1
        color: ThemeColors.surfaceTranslucent
        visible: networkPopoutRoot.availableNetworks.length > 0
    }

    ColumnLayout {
        spacing: 2
        visible: networkPopoutRoot.availableNetworks.length > 0

        Text {
            text: "Available Networks"
            font.pixelSize: 11
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.dim
        }

        Repeater {
            model: networkPopoutRoot.availableNetworks

            RowLayout {
                required property var modelData

                Layout.fillWidth: true
                spacing: 8

                Text {
                    Layout.fillWidth: true
                    text: modelData.ssid
                    font.pixelSize: 12
                    font.family: "JetBrainsMono Nerd Font"
                    color: modelData.ssid === networkPopoutRoot.currentSsid ? ThemeColors.accent : ThemeColors.foreground
                    elide: Text.ElideRight
                }

                Text {
                    text: modelData.signal + "%"
                    font.pixelSize: 11
                    font.family: "JetBrainsMono Nerd Font"
                    color: ThemeColors.dim
                }

                Text {
                    text: modelData.security !== "" ? "󰌾" : ""
                    font.pixelSize: 12
                    font.family: "JetBrainsMono Nerd Font"
                    color: ThemeColors.dim
                    visible: modelData.security !== ""
                }
            }
        }
    }
}
