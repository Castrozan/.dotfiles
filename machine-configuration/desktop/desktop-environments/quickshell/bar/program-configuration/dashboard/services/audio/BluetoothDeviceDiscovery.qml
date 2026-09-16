import Quickshell
import Quickshell.Io

Scope {
    id: bluetoothDiscoveryRoot

    required property var previousPairedDevices

    signal pairedDevicesDiscovered(var devices)
    signal adapterPowerDiscovered(bool powered)

    function refresh(): void {
        listPairedDevicesProcess.running = true;
        listConnectedDevicesProcess.running = true;
        adapterStateProcess.running = true;
    }

    property var _pairedDevicesList: []
    property var _connectedMacs: ({})

    function _mergePairedDevices(): void {
        const merged = _pairedDevicesList.map(device => ({
                    mac: device.mac,
                    name: device.name,
                    connected: _connectedMacs[device.mac] === true
                }));
        merged.sort((a, b) => (b.connected ? 1 : 0) - (a.connected ? 1 : 0));
        if (merged.length > 0 || previousPairedDevices.length === 0)
            pairedDevicesDiscovered(merged);
    }

    Process {
        id: listPairedDevicesProcess
        command: ["bluetoothctl", "devices"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const lines = data.trim().split("\n");
                const devices = [];
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (line === "")
                        continue;
                    const parts = line.split(" ");
                    if (parts.length >= 3)
                        devices.push({
                            mac: parts[1],
                            name: parts.slice(2).join(" ")
                        });
                }
                devices.sort((a, b) => a.mac.localeCompare(b.mac));
                bluetoothDiscoveryRoot._pairedDevicesList = devices;
                bluetoothDiscoveryRoot._mergePairedDevices();
            }
        }
    }

    Process {
        id: listConnectedDevicesProcess
        command: ["bluetoothctl", "devices", "Connected"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const lines = data.trim().split("\n");
                const macs = {};
                for (let i = 0; i < lines.length; i++) {
                    const parts = lines[i].trim().split(" ");
                    if (parts.length >= 2)
                        macs[parts[1]] = true;
                }
                bluetoothDiscoveryRoot._connectedMacs = macs;
                bluetoothDiscoveryRoot._mergePairedDevices();
            }
        }
    }

    Process {
        id: adapterStateProcess
        command: ["bluetoothctl", "show"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                bluetoothDiscoveryRoot.adapterPowerDiscovered(data.indexOf("Powered: yes") !== -1);
            }
        }
    }
}
