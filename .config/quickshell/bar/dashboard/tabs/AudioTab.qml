pragma ComponentBehavior: Bound

import "../components"
import "../services"
import ".."
import Quickshell.Io
import QtQuick
import QtQuick.Layouts

Item {
    id: audioTabRoot

    property bool dashboardIsActive: false

    implicitWidth: Math.max(520, audioContentColumn.implicitWidth)
    implicitHeight: audioContentColumn.implicitHeight

    Component.onDestruction: {
        if (audioTabRoot.dashboardIsActive)
            AudioService.refCount--;
    }

    Connections {
        target: audioTabRoot
        function onDashboardIsActiveChanged() {
            if (audioTabRoot.dashboardIsActive)
                AudioService.refCount++;
            else
                AudioService.refCount--;
        }
    }

    ColumnLayout {
        id: audioContentColumn

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Appearance.spacing.normal
        focus: true

            AudioSectionHeader {
                iconName: "volume_up"
                title: "Output Devices"
            }

            ColumnLayout {
                id: outputDevicesColumn
                Layout.fillWidth: true
                spacing: Appearance.spacing.small

                Repeater {
                    id: outputDevicesRepeater
                    model: AudioService.sinks

                    AudioDeviceCard {
                        required property var modelData
                        required property int index

                        Layout.fillWidth: true
                        deviceName: modelData.name
                        deviceDescription: modelData.description
                        devicePortType: modelData.portType
                        deviceVolume: modelData.volume
                        deviceMuted: modelData.mute
                        deviceIsBluetooth: modelData.isBluetooth
                        deviceIsDefault: modelData.name === AudioService.defaultSinkName
                        isOutputDevice: true

                        KeyNavigation.up: index > 0 ? outputDevicesRepeater.itemAt(index - 1) : null
                        KeyNavigation.down: index < outputDevicesRepeater.count - 1 ? outputDevicesRepeater.itemAt(index + 1) : (inputDevicesRepeater.count > 0 ? inputDevicesRepeater.itemAt(0) : (bluetoothDevicesRepeater.count > 0 ? bluetoothDevicesRepeater.itemAt(0) : null))
                    }
                }
            }

            AudioSectionHeader {
                Layout.topMargin: Appearance.spacing.small
                iconName: "mic"
                title: "Input Devices"
            }

            ColumnLayout {
                id: inputDevicesColumn
                Layout.fillWidth: true
                spacing: Appearance.spacing.small

                Repeater {
                    id: inputDevicesRepeater
                    model: AudioService.sources

                    AudioDeviceCard {
                        required property var modelData
                        required property int index

                        Layout.fillWidth: true
                        deviceName: modelData.name
                        deviceDescription: modelData.description
                        devicePortType: modelData.portType
                        deviceVolume: modelData.volume
                        deviceMuted: modelData.mute
                        deviceIsBluetooth: modelData.isBluetooth
                        deviceIsDefault: modelData.name === AudioService.defaultSourceName
                        isOutputDevice: false

                        KeyNavigation.up: index > 0 ? inputDevicesRepeater.itemAt(index - 1) : (outputDevicesRepeater.count > 0 ? outputDevicesRepeater.itemAt(outputDevicesRepeater.count - 1) : null)
                        KeyNavigation.down: index < inputDevicesRepeater.count - 1 ? inputDevicesRepeater.itemAt(index + 1) : (bluetoothDevicesRepeater.count > 0 ? bluetoothDevicesRepeater.itemAt(0) : null)
                    }
                }
            }

            AudioSectionHeader {
                Layout.topMargin: Appearance.spacing.small
                iconName: "bluetooth"
                title: "Bluetooth"
                visible: AudioService.pairedDevices.length > 0
            }

            ColumnLayout {
                id: bluetoothDevicesColumn
                Layout.fillWidth: true
                spacing: Appearance.spacing.small
                visible: AudioService.pairedDevices.length > 0

                Repeater {
                    id: bluetoothDevicesRepeater
                    model: AudioService.pairedDevices

                    BluetoothDeviceCard {
                        required property var modelData
                        required property int index

                        Layout.fillWidth: true
                        deviceMac: modelData.mac
                        deviceName: modelData.name
                        deviceConnected: modelData.connected

                        KeyNavigation.up: index > 0 ? bluetoothDevicesRepeater.itemAt(index - 1) : (inputDevicesRepeater.count > 0 ? inputDevicesRepeater.itemAt(inputDevicesRepeater.count - 1) : (outputDevicesRepeater.count > 0 ? outputDevicesRepeater.itemAt(outputDevicesRepeater.count - 1) : null))
                        KeyNavigation.down: index < bluetoothDevicesRepeater.count - 1 ? bluetoothDevicesRepeater.itemAt(index + 1) : null
                    }
                }
            }
        }

    component AudioSectionHeader: RowLayout {
        property string iconName
        property string title

        Layout.fillWidth: true
        spacing: Appearance.spacing.small

        MaterialIcon {
            text: parent.iconName
            fill: 1
            color: Colours.palette.m3primary
            font.pointSize: Appearance.font.size.large
        }

        StyledText {
            Layout.fillWidth: true
            text: parent.title
            font.pointSize: Appearance.font.size.normal
            font.weight: Font.Medium
            color: Colours.palette.m3onSurface
        }
    }

    component AudioDeviceCard: StyledRect {
        id: audioDeviceCardRoot

        property string deviceName
        property string deviceDescription
        property string devicePortType
        property int deviceVolume: 0
        property bool deviceMuted: false
        property bool deviceIsBluetooth: false
        property bool deviceIsDefault: false
        property bool isOutputDevice: true

        color: Colours.tPalette.m3surfaceContainer
        radius: Appearance.rounding.large
        clip: true
        focus: true
        implicitHeight: audioDeviceCardLayout.implicitHeight + Appearance.padding.large * 2
        implicitWidth: 520

        border.width: activeFocus ? 2 : 0
        border.color: Colours.palette.m3primary

        Keys.onReturnPressed: {
            if (isOutputDevice)
                AudioService.setDefaultSink(deviceName);
            else
                AudioService.setDefaultSource(deviceName);
        }

        Keys.onSpacePressed: {
            if (isOutputDevice)
                AudioService.toggleSinkMute(deviceName);
            else
                AudioService.toggleSourceMute(deviceName);
        }

        Keys.onLeftPressed: {
            const newVolume = Math.max(0, deviceVolume - 5);
            if (isOutputDevice)
                AudioService.setSinkVolume(deviceName, newVolume);
            else
                AudioService.setSourceVolume(deviceName, newVolume);
        }

        Keys.onRightPressed: {
            const newVolume = Math.min(150, deviceVolume + 5);
            if (isOutputDevice)
                AudioService.setSinkVolume(deviceName, newVolume);
            else
                AudioService.setSourceVolume(deviceName, newVolume);
        }

        StyledRect {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: Colours.palette.m3primary
            visible: audioDeviceCardRoot.deviceIsDefault
            radius: Appearance.rounding.full
        }

        StyledRect {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: parent.width * (audioDeviceCardRoot.deviceVolume / 150.0)
            color: Qt.alpha(Colours.palette.m3primary, 0.08)
            visible: !audioDeviceCardRoot.deviceMuted

            Behavior on width {
                Anim {
                    duration: Appearance.anim.durations.normal
                }
            }
        }

        RowLayout {
            id: audioDeviceCardLayout

            anchors.fill: parent
            anchors.margins: Appearance.padding.large
            spacing: Appearance.spacing.normal

            IconButton {
                id: audioDeviceMuteButton

                type: IconButton.Text
                icon: {
                    if (audioDeviceCardRoot.isOutputDevice)
                        return audioDeviceCardRoot.deviceMuted ? "volume_off" : "volume_up";
                    return audioDeviceCardRoot.deviceMuted ? "mic_off" : "mic";
                }
                inactiveOnColour: audioDeviceCardRoot.deviceMuted ? Colours.palette.m3error : Colours.palette.m3primary
                font.pointSize: Appearance.font.size.large
                focusPolicy: Qt.NoFocus

                onClicked: {
                    if (audioDeviceCardRoot.isOutputDevice)
                        AudioService.toggleSinkMute(audioDeviceCardRoot.deviceName);
                    else
                        AudioService.toggleSourceMute(audioDeviceCardRoot.deviceName);
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Appearance.spacing.smaller

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Appearance.spacing.small

                    StyledText {
                        Layout.fillWidth: true
                        text: audioDeviceCardRoot.deviceDescription
                        font.pointSize: Appearance.font.size.normal
                        font.weight: audioDeviceCardRoot.deviceIsDefault ? Font.Medium : Font.Normal
                        color: audioDeviceCardRoot.deviceIsDefault ? Colours.palette.m3primary : Colours.palette.m3onSurface
                        elide: Text.ElideRight
                    }

                    StyledText {
                        text: audioDeviceCardRoot.deviceVolume + "%"
                        font.pointSize: Appearance.font.size.small
                        font.weight: Font.Medium
                        color: audioDeviceCardRoot.deviceMuted ? Colours.palette.m3error : audioDeviceCardRoot.deviceVolume > 100 ? Colours.palette.m3error : Colours.palette.m3onSurfaceVariant
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Appearance.spacing.small

                    MaterialIcon {
                        text: audioDeviceCardRoot.deviceIsBluetooth ? "bluetooth" : audioDeviceCardRoot.devicePortType.toLowerCase() === "headset" ? "headphones" : audioDeviceCardRoot.isOutputDevice ? "speaker" : "settings_voice"
                        font.pointSize: Appearance.font.size.small
                        color: Colours.palette.m3onSurfaceVariant
                    }

                    StyledText {
                        text: {
                            if (audioDeviceCardRoot.deviceIsBluetooth)
                                return "Bluetooth";
                            if (audioDeviceCardRoot.devicePortType)
                                return audioDeviceCardRoot.devicePortType;
                            return audioDeviceCardRoot.isOutputDevice ? "Output" : "Input";
                        }
                        font.pointSize: Appearance.font.size.smaller
                        color: Colours.palette.m3onSurfaceVariant
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    StyledText {
                        text: audioDeviceCardRoot.deviceIsDefault ? "Default" : ""
                        font.pointSize: Appearance.font.size.smaller
                        font.weight: Font.Medium
                        color: Colours.palette.m3primary
                        visible: audioDeviceCardRoot.deviceIsDefault
                    }
                }

                StyledSlider {
                    Layout.fillWidth: true
                    implicitHeight: Appearance.padding.normal * 2.5
                    from: 0
                    to: 1.5
                    value: audioDeviceCardRoot.deviceVolume / 100.0
                    focusPolicy: Qt.NoFocus

                    onMoved: {
                        const percent = Math.round(value * 100);
                        if (audioDeviceCardRoot.isOutputDevice)
                            AudioService.setSinkVolume(audioDeviceCardRoot.deviceName, percent);
                        else
                            AudioService.setSourceVolume(audioDeviceCardRoot.deviceName, percent);
                    }
                }
            }

            IconButton {
                id: audioDeviceDefaultButton

                type: IconButton.Text
                icon: audioDeviceCardRoot.deviceIsDefault ? "star" : "star_outline"
                inactiveOnColour: audioDeviceCardRoot.deviceIsDefault ? Colours.palette.m3primary : Colours.palette.m3onSurfaceVariant
                font.pointSize: Appearance.font.size.large
                focusPolicy: Qt.NoFocus

                onClicked: {
                    if (audioDeviceCardRoot.isOutputDevice)
                        AudioService.setDefaultSink(audioDeviceCardRoot.deviceName);
                    else
                        AudioService.setDefaultSource(audioDeviceCardRoot.deviceName);
                }
            }
        }

        StateLayer {
            color: Colours.palette.m3onSurface
            showHoverBackground: true
            function onClicked(): void {
                audioDeviceCardRoot.forceActiveFocus();
            }
        }
    }

    component BluetoothDeviceCard: StyledRect {
        id: bluetoothDeviceCardRoot

        property string deviceMac
        property string deviceName
        property bool deviceConnected: false

        readonly property var associatedCard: AudioService.cardForBluetoothMac(deviceMac)
        readonly property bool hasProfiles: associatedCard !== null && associatedCard.profiles.length > 0

        color: Colours.tPalette.m3surfaceContainer
        radius: Appearance.rounding.large
        clip: true
        focus: true
        implicitHeight: bluetoothDeviceCardLayout.implicitHeight + Appearance.padding.large * 2
        implicitWidth: 520

        border.width: activeFocus ? 2 : 0
        border.color: Colours.palette.m3primary

        Keys.onReturnPressed: {
            if (deviceConnected)
                AudioService.disconnectDevice(deviceMac);
            else
                AudioService.connectDevice(deviceMac);
        }

        Keys.onSpacePressed: Keys.onReturnPressed(event)

        StyledRect {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: Colours.palette.m3primary
            visible: bluetoothDeviceCardRoot.deviceConnected
            radius: Appearance.rounding.full
        }

        ColumnLayout {
            id: bluetoothDeviceCardLayout

            anchors.fill: parent
            anchors.margins: Appearance.padding.large
            spacing: Appearance.spacing.small

            RowLayout {
                Layout.fillWidth: true
                spacing: Appearance.spacing.normal

                MaterialIcon {
                    text: bluetoothDeviceCardRoot.deviceConnected ? "bluetooth_connected" : "bluetooth"
                    fill: bluetoothDeviceCardRoot.deviceConnected ? 1 : 0
                    color: bluetoothDeviceCardRoot.deviceConnected ? Colours.palette.m3primary : Colours.palette.m3onSurfaceVariant
                    font.pointSize: Appearance.font.size.large
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0

                    StyledText {
                        Layout.fillWidth: true
                        text: bluetoothDeviceCardRoot.deviceName
                        font.pointSize: Appearance.font.size.normal
                        font.weight: bluetoothDeviceCardRoot.deviceConnected ? Font.Medium : Font.Normal
                        color: bluetoothDeviceCardRoot.deviceConnected ? Colours.palette.m3primary : Colours.palette.m3onSurface
                        elide: Text.ElideRight
                    }

                    StyledText {
                        text: bluetoothDeviceCardRoot.deviceConnected ? "Connected" : "Paired"
                        font.pointSize: Appearance.font.size.smaller
                        color: Colours.palette.m3onSurfaceVariant
                    }
                }

                IconButton {
                    type: IconButton.Tonal
                    icon: bluetoothDeviceCardRoot.deviceConnected ? "link_off" : "link"
                    font.pointSize: Appearance.font.size.normal
                    implicitWidth: 36
                    implicitHeight: 36
                    focusPolicy: Qt.NoFocus

                    onClicked: {
                        if (bluetoothDeviceCardRoot.deviceConnected)
                            AudioService.disconnectDevice(bluetoothDeviceCardRoot.deviceMac);
                        else
                            AudioService.connectDevice(bluetoothDeviceCardRoot.deviceMac);
                    }
                }
            }

            Flow {
                Layout.fillWidth: true
                spacing: Appearance.spacing.smaller
                visible: bluetoothDeviceCardRoot.deviceConnected && bluetoothDeviceCardRoot.hasProfiles

                Repeater {
                    model: bluetoothDeviceCardRoot.associatedCard?.profiles ?? []

                    AudioProfileChip {
                        required property var modelData

                        profileName: modelData.name
                        profileDescription: _shortenProfileDescription(modelData.description)
                        profileIsActive: modelData.name === bluetoothDeviceCardRoot.associatedCard?.activeProfile

                        onActivated: AudioService.setCardProfile(bluetoothDeviceCardRoot.associatedCard.name, modelData.name)
                    }
                }
            }
        }

        StateLayer {
            color: Colours.palette.m3onSurface
            showHoverBackground: true
            function onClicked(): void {
                bluetoothDeviceCardRoot.forceActiveFocus();
            }
        }
    }

    component AudioProfileChip: StyledRect {
        id: audioProfileChipRoot

        property string profileName
        property string profileDescription
        property bool profileIsActive: false

        signal activated()

        implicitWidth: audioProfileChipLabel.implicitWidth + Appearance.padding.normal * 2
        implicitHeight: audioProfileChipLabel.implicitHeight + Appearance.padding.smaller * 2
        radius: Appearance.rounding.full
        color: profileIsActive ? Colours.palette.m3primary : Colours.palette.m3secondaryContainer

        StyledText {
            id: audioProfileChipLabel

            anchors.centerIn: parent
            text: audioProfileChipRoot.profileDescription
            font.pointSize: Appearance.font.size.smaller
            font.weight: audioProfileChipRoot.profileIsActive ? Font.Medium : Font.Normal
            color: audioProfileChipRoot.profileIsActive ? Colours.palette.m3onPrimary : Colours.palette.m3onSecondaryContainer
        }

        StateLayer {
            color: audioProfileChipRoot.profileIsActive ? Colours.palette.m3onPrimary : Colours.palette.m3onSecondaryContainer
            function onClicked(): void {
                audioProfileChipRoot.activated();
            }
        }
    }

    function _shortenProfileDescription(description: string): string {
        if (description.indexOf("SBC-XQ") !== -1)
            return "SBC-XQ";
        if (description.indexOf("SBC") !== -1)
            return "SBC";
        if (description.indexOf("AAC") !== -1)
            return "AAC";
        if (description.indexOf("mSBC") !== -1)
            return "mSBC";
        if (description.indexOf("CVSD") !== -1)
            return "CVSD";
        if (description.indexOf("LDAC") !== -1)
            return "LDAC";
        if (description.indexOf("aptX HD") !== -1)
            return "aptX HD";
        if (description.indexOf("aptX") !== -1)
            return "aptX";
        if (description.indexOf("A2DP") !== -1)
            return "A2DP";
        if (description.indexOf("HSP") !== -1 || description.indexOf("HFP") !== -1)
            return "HSP/HFP";
        if (description.indexOf("Headset Head Unit") !== -1)
            return "Headset";
        if (description.indexOf("High Fidelity") !== -1)
            return "HiFi";
        return description.length > 12 ? description.substring(0, 10) + "…" : description;
    }
}
