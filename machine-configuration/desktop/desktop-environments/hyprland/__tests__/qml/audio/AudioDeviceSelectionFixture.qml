import QtQuick

QtObject {

    property var sinks: []
    property string defaultSinkName: ""
    property var cards: []
    property var pairedDevices: []
    property var _pairedDevicesList: []
    property var _connectedMacs: ({})

    readonly property var defaultSink: {
        for (let i = 0; i < sinks.length; i++)
            if (sinks[i].name === defaultSinkName)
                return sinks[i];
        return null;
    }

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

    function cardForBluetoothMac(macAddress) {
        const normalizedMac = macAddress.replace(/:/g, "_");
        for (let i = 0; i < cards.length; i++)
            if (cards[i].name.indexOf(normalizedMac) !== -1)
                return cards[i];
        return null;
    }
}
