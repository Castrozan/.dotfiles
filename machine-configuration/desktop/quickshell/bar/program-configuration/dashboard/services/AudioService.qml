pragma Singleton

import ".."
import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: audioServiceRoot

    property var sinks: []
    property string defaultSinkName: ""
    property var sources: []
    property string defaultSourceName: ""
    property var cards: []
    property var pairedDevices: []
    property bool adapterPowered: true

    property int refCount: 0
    property string pendingBluetoothMac: ""

    readonly property var defaultSink: {
        for (let i = 0; i < sinks.length; i++)
            if (sinks[i].name === defaultSinkName)
                return sinks[i];
        return null;
    }

    readonly property var defaultSource: {
        for (let i = 0; i < sources.length; i++)
            if (sources[i].name === defaultSourceName)
                return sources[i];
        return null;
    }

    readonly property bool defaultSinkMuted: defaultSink?.mute ?? false
    readonly property bool defaultSourceMuted: defaultSource?.mute ?? false
    readonly property bool defaultSinkIsBluetooth: defaultSinkName.startsWith("bluez_")

    readonly property string defaultSinkDeviceType: {
        if (!defaultSink)
            return "speaker";
        if (defaultSinkName.startsWith("bluez_"))
            return "bluetooth";
        const portType = (defaultSink.portType ?? "").toLowerCase();
        if (portType === "headset" || portType === "headphones")
            return "headphones";
        return "speaker";
    }

    function refresh(): void {
        listSinksProcess.running = true;
        listSourcesProcess.running = true;
        getDefaultSinkProcess.running = true;
        getDefaultSourceProcess.running = true;
        listCardsProcess.running = true;
        listPairedDevicesProcess.running = true;
        listConnectedDevicesProcess.running = true;
        adapterStateProcess.running = true;
    }

    function setDefaultSink(sinkName: string): void {
        sinkActionProcess.command = ["pactl", "set-default-sink", sinkName];
        sinkActionProcess.running = true;
    }

    function setDefaultSource(sourceName: string): void {
        sourceActionProcess.command = ["pactl", "set-default-source", sourceName];
        sourceActionProcess.running = true;
    }

    function setSinkVolume(sinkName: string, percent: int): void {
        volumeActionProcess.command = ["pactl", "set-sink-volume", sinkName, percent + "%"];
        volumeActionProcess.running = true;
    }

    function setSourceVolume(sourceName: string, percent: int): void {
        volumeActionProcess.command = ["pactl", "set-source-volume", sourceName, percent + "%"];
        volumeActionProcess.running = true;
    }

    function toggleSinkMute(sinkName: string): void {
        muteActionProcess.command = ["pactl", "set-sink-mute", sinkName, "toggle"];
        muteActionProcess.running = true;
    }

    function toggleSourceMute(sourceName: string): void {
        muteActionProcess.command = ["pactl", "set-source-mute", sourceName, "toggle"];
        muteActionProcess.running = true;
    }

    function setCardProfile(cardName: string, profileName: string): void {
        profileActionProcess.command = ["pactl", "set-card-profile", cardName, profileName];
        profileActionProcess.running = true;
    }

    function connectDevice(macAddress: string): void {
        pendingBluetoothMac = macAddress;
        bluetoothActionProcess.command = ["bluetoothctl", "connect", macAddress];
        bluetoothActionProcess.running = true;
    }

    function disconnectDevice(macAddress: string): void {
        pendingBluetoothMac = macAddress;
        bluetoothActionProcess.command = ["bluetoothctl", "disconnect", macAddress];
        bluetoothActionProcess.running = true;
    }

    function cardForBluetoothMac(macAddress: string): var {
        const normalizedMac = macAddress.replace(/:/g, "_");
        for (let i = 0; i < cards.length; i++)
            if (cards[i].name.indexOf(normalizedMac) !== -1)
                return cards[i];
        return null;
    }

    Process {
        id: sinkActionProcess
        onExited: audioServiceRoot.refresh()
    }

    Process {
        id: sourceActionProcess
        onExited: audioServiceRoot.refresh()
    }

    Process {
        id: volumeActionProcess
    }

    Process {
        id: muteActionProcess
        onExited: audioServiceRoot.refresh()
    }

    Process {
        id: profileActionProcess
        onExited: audioServiceRoot.refresh()
    }

    Process {
        id: bluetoothActionProcess
        onExited: {
            audioServiceRoot.pendingBluetoothMac = "";
            audioServiceRoot.refresh();
        }
    }

    Process {
        id: listSinksProcess
        command: ["env", "LC_ALL=C", "pactl", "--format=json", "list", "sinks"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    const parsed = JSON.parse(data);
                    const newSinks = parsed.map(sink => ({
                        index: sink.index,
                        name: sink.name,
                        description: sink.description ?? "",
                        mute: sink.mute ?? false,
                        volume: _extractVolumePercent(sink.volume),
                        state: sink.state ?? "",
                        portType: _extractPortType(sink.ports, sink.active_port),
                        isBluetooth: (sink.name ?? "").startsWith("bluez_")
                    }));
                    if (!_audioDeviceListsAreEqual(audioServiceRoot.sinks, newSinks))
                        audioServiceRoot.sinks = newSinks;
                } catch (e) {}
            }
        }
    }

    Process {
        id: listSourcesProcess
        command: ["env", "LC_ALL=C", "pactl", "--format=json", "list", "sources"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    const parsed = JSON.parse(data);
                    const newSources = parsed
                        .filter(source => (source.name ?? "").indexOf(".monitor") === -1)
                        .map(source => ({
                            index: source.index,
                            name: source.name,
                            description: source.description ?? "",
                            mute: source.mute ?? false,
                            volume: _extractVolumePercent(source.volume),
                            state: source.state ?? "",
                            portType: _extractPortType(source.ports, source.active_port),
                            isBluetooth: (source.name ?? "").startsWith("bluez_")
                        }));
                    if (!_audioDeviceListsAreEqual(audioServiceRoot.sources, newSources))
                        audioServiceRoot.sources = newSources;
                } catch (e) {}
            }
        }
    }

    Process {
        id: getDefaultSinkProcess
        command: ["pactl", "get-default-sink"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                audioServiceRoot.defaultSinkName = data.trim();
            }
        }
    }

    Process {
        id: getDefaultSourceProcess
        command: ["pactl", "get-default-source"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                audioServiceRoot.defaultSourceName = data.trim();
            }
        }
    }

    Process {
        id: listCardsProcess
        command: ["env", "LC_ALL=C", "pactl", "--format=json", "list", "cards"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    const parsed = JSON.parse(data);
                    audioServiceRoot.cards = parsed.map(card => {
                        const availableProfiles = [];
                        const profilesObject = card.profiles ?? {};
                        for (const profileName in profilesObject) {
                            const profile = profilesObject[profileName];
                            if (profile.available !== false && profileName !== "off")
                                availableProfiles.push({
                                    name: profileName,
                                    description: profile.description ?? profileName
                                });
                        }
                        return {
                            index: card.index,
                            name: card.name ?? "",
                            activeProfile: card.active_profile ?? "",
                            profiles: availableProfiles
                        };
                    });
                } catch (e) {}
            }
        }
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
        if (merged.length > 0 || pairedDevices.length === 0)
            pairedDevices = merged;
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
                audioServiceRoot._pairedDevicesList = devices;
                audioServiceRoot._mergePairedDevices();
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
                audioServiceRoot._connectedMacs = macs;
                audioServiceRoot._mergePairedDevices();
            }
        }
    }

    Process {
        id: adapterStateProcess
        command: ["bluetoothctl", "show"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                audioServiceRoot.adapterPowered = data.indexOf("Powered: yes") !== -1;
            }
        }
    }

    Timer {
        running: audioServiceRoot.refCount > 0
        interval: DashboardConfig.audioUpdateInterval
        repeat: true
        triggeredOnStart: true
        onTriggered: audioServiceRoot.refresh()
    }

    function _audioDeviceListsAreEqual(oldList: var, newList: var): bool {
        if (oldList.length !== newList.length)
            return false;
        for (let i = 0; i < oldList.length; i++) {
            const oldItem = oldList[i];
            const newItem = newList[i];
            if (oldItem.name !== newItem.name || oldItem.volume !== newItem.volume || oldItem.mute !== newItem.mute || oldItem.state !== newItem.state || oldItem.description !== newItem.description)
                return false;
        }
        return true;
    }

    function _extractVolumePercent(volumeObject: var): int {
        if (!volumeObject)
            return 0;
        for (const channel in volumeObject) {
            const percentString = volumeObject[channel].value_percent ?? "0%";
            return parseInt(percentString) || 0;
        }
        return 0;
    }

    function _extractPortType(ports: var, activePortName: var): string {
        if (!ports || !activePortName)
            return "";
        for (let i = 0; i < ports.length; i++)
            if (ports[i].name === activePortName)
                return ports[i].type ?? "";
        return "";
    }
}
