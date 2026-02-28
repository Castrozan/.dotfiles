import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: bluetoothPopoutRoot

    property bool active: false

    property bool adapterPowered: true
    property var connectedDevices: []

    spacing: 12

    onActiveChanged: {
        if (active) {
            fetchAdapterStateProcess.running = true;
            fetchConnectedDevicesProcess.running = true;
        }
    }

    Process {
        id: fetchAdapterStateProcess
        command: ["bluetoothctl", "show"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const dataWithoutAnsiEscapeCodes = data.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, "");
                bluetoothPopoutRoot.adapterPowered = dataWithoutAnsiEscapeCodes.indexOf("Powered: yes") !== -1;
            }
        }
    }

    Process {
        id: fetchConnectedDevicesProcess
        command: ["bluetoothctl", "devices", "Connected"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const dataWithoutAnsiEscapeCodes = data.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, "");
                let lines = dataWithoutAnsiEscapeCodes.trim().split("\n");
                let devices = [];
                for (let i = 0; i < lines.length; i++) {
                    let line = lines[i].trim();
                    if (line === "") continue;
                    let parts = line.split(" ");
                    if (parts.length >= 3) {
                        devices.push({
                            mac: parts[1],
                            name: parts.slice(2).join(" ")
                        });
                    }
                }
                bluetoothPopoutRoot.connectedDevices = devices;
            }
        }
    }

    Text {
        text: "Bluetooth"
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    RowLayout {
        spacing: 8

        Text {
            text: bluetoothPopoutRoot.adapterPowered ? "Adapter: On" : "Adapter: Off"
            font.pixelSize: 12
            font.family: "JetBrainsMono Nerd Font"
            color: bluetoothPopoutRoot.adapterPowered ? ThemeColors.accent : ThemeColors.dim
        }
    }

    Rectangle {
        Layout.fillWidth: true
        height: 1
        color: ThemeColors.surfaceTranslucent
        visible: bluetoothPopoutRoot.connectedDevices.length > 0
    }

    ColumnLayout {
        spacing: 4
        visible: bluetoothPopoutRoot.connectedDevices.length > 0

        Text {
            text: "Connected Devices"
            font.pixelSize: 11
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.dim
        }

        Repeater {
            model: bluetoothPopoutRoot.connectedDevices

            RowLayout {
                required property var modelData

                Layout.fillWidth: true
                spacing: 8

                Text {
                    text: "󰂱"
                    font.pixelSize: 14
                    font.family: "JetBrainsMono Nerd Font"
                    color: ThemeColors.accent
                }

                Text {
                    Layout.fillWidth: true
                    text: modelData.name
                    font.pixelSize: 12
                    font.family: "JetBrainsMono Nerd Font"
                    color: ThemeColors.foreground
                    elide: Text.ElideRight
                }
            }
        }
    }

    Text {
        text: "No devices connected"
        font.pixelSize: 12
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.dim
        visible: bluetoothPopoutRoot.connectedDevices.length === 0 && bluetoothPopoutRoot.adapterPowered
    }
}
