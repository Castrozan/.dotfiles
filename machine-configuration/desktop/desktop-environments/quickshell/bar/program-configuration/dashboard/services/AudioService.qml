pragma Singleton

import ".."
import "audio"
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
        pulseAudioDiscovery.refresh();
        bluetoothDeviceDiscovery.refresh();
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

    PulseAudioDiscovery {
        id: pulseAudioDiscovery
        previousSinks: audioServiceRoot.sinks
        previousSources: audioServiceRoot.sources
        onSinksDiscovered: devices => audioServiceRoot.sinks = devices
        onSourcesDiscovered: devices => audioServiceRoot.sources = devices
        onDefaultSinkNameDiscovered: name => audioServiceRoot.defaultSinkName = name
        onDefaultSourceNameDiscovered: name => audioServiceRoot.defaultSourceName = name
        onCardsDiscovered: cards => audioServiceRoot.cards = cards
    }

    BluetoothDeviceDiscovery {
        id: bluetoothDeviceDiscovery
        previousPairedDevices: audioServiceRoot.pairedDevices
        onPairedDevicesDiscovered: devices => audioServiceRoot.pairedDevices = devices
        onAdapterPowerDiscovered: powered => audioServiceRoot.adapterPowered = powered
    }

    Timer {
        running: audioServiceRoot.refCount > 0
        interval: DashboardConfig.audioUpdateInterval
        repeat: true
        triggeredOnStart: true
        onTriggered: audioServiceRoot.refresh()
    }
}
