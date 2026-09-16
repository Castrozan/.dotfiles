pragma ComponentBehavior: Bound

import "audio"
import "../services"
import ".."
import QtQuick
import QtQuick.Layouts

Item {
    id: audioTabRoot

    property bool dashboardIsActive: false

    readonly property int maximumTabHeight: 700

    implicitWidth: Math.max(800, audioContentColumn.implicitWidth)
    implicitHeight: Math.min(maximumTabHeight, audioContentColumn.implicitHeight)

    onDashboardIsActiveChanged: {
        if (dashboardIsActive)
            AudioService.refCount++;
        else
            AudioService.refCount--;
    }

    Component.onDestruction: {
        if (audioTabRoot.dashboardIsActive)
            AudioService.refCount--;
    }

    function ensureItemVisible(item: var): void {
        const itemPos = item.mapToItem(audioContentColumn, 0, 0);
        const itemTop = itemPos.y;
        const itemBottom = itemTop + item.height;
        if (itemTop < audioScrollArea.contentY)
            audioScrollArea.contentY = Math.max(0, itemTop - Appearance.spacing.normal);
        else if (itemBottom > audioScrollArea.contentY + audioScrollArea.height)
            audioScrollArea.contentY = Math.min(audioScrollArea.contentHeight - audioScrollArea.height, itemBottom - audioScrollArea.height + Appearance.spacing.normal);
    }

    function activateKeyboardNavigation(): void {
        if (outputDevicesRepeater.count > 0)
            outputDevicesRepeater.itemAt(0).forceActiveFocus();
        else if (inputDevicesRepeater.count > 0)
            inputDevicesRepeater.itemAt(0).forceActiveFocus();
        else if (bluetoothDevicesRepeater.count > 0)
            bluetoothDevicesRepeater.itemAt(0).forceActiveFocus();
    }

    Flickable {
        id: audioScrollArea

        anchors.fill: parent
        contentWidth: width
        contentHeight: audioContentColumn.implicitHeight
        flickableDirection: Flickable.VerticalFlick
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        Keys.onPressed: event => {
            if (event.key === Qt.Key_PageDown) {
                audioScrollArea.contentY = Math.min(audioScrollArea.contentY + 100, audioScrollArea.contentHeight - audioScrollArea.height);
                event.accepted = true;
            } else if (event.key === Qt.Key_PageUp) {
                audioScrollArea.contentY = Math.max(audioScrollArea.contentY - 100, 0);
                event.accepted = true;
            }
        }

        ColumnLayout {
            id: audioContentColumn

            width: audioScrollArea.width
            spacing: Appearance.spacing.normal

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

                        onFocusRequested: item => audioTabRoot.ensureItemVisible(item)

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

                        onFocusRequested: item => audioTabRoot.ensureItemVisible(item)

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

                        onFocusRequested: item => audioTabRoot.ensureItemVisible(item)

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
    }
}
