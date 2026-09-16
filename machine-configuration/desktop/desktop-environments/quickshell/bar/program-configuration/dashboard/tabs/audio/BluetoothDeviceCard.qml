pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

import "AudioProfileDescription.js" as AudioProfileDescription

StyledRect {
    id: bluetoothDeviceCardRoot

    signal focusRequested(var item)

    property string deviceMac
    property string deviceName
    property bool deviceConnected: false

    readonly property var associatedCard: AudioService.cardForBluetoothMac(deviceMac)
    readonly property bool hasProfiles: associatedCard !== null && associatedCard.profiles.length > 0
    readonly property bool isPending: AudioService.pendingBluetoothMac === deviceMac

    color: Colours.tPalette.m3surfaceContainer
    radius: Appearance.rounding.large
    clip: true
    focus: true
    implicitHeight: bluetoothDeviceCardLayout.implicitHeight + Appearance.padding.large * 2
    implicitWidth: 800

    border.width: activeFocus ? 2 : 0
    border.color: Colours.palette.m3primary

    onActiveFocusChanged: {
        if (activeFocus)
            focusRequested(bluetoothDeviceCardRoot);
    }

    function toggleConnection(): void {
        if (isPending)
            return;
        if (deviceConnected)
            AudioService.disconnectDevice(deviceMac);
        else
            AudioService.connectDevice(deviceMac);
    }

    StateLayer {
        color: Colours.palette.m3onSurface
        showHoverBackground: true
        function onClicked(): void {
            bluetoothDeviceCardRoot.forceActiveFocus();
            bluetoothDeviceCardRoot.toggleConnection();
        }
    }

    Keys.onReturnPressed: toggleConnection()
    Keys.onSpacePressed: toggleConnection()

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
                text: bluetoothDeviceCardRoot.isPending ? "bluetooth_searching" : bluetoothDeviceCardRoot.deviceConnected ? "bluetooth_connected" : "bluetooth"
                fill: bluetoothDeviceCardRoot.deviceConnected ? 1 : 0
                color: bluetoothDeviceCardRoot.isPending ? Colours.palette.m3tertiary : bluetoothDeviceCardRoot.deviceConnected ? Colours.palette.m3primary : Colours.palette.m3onSurfaceVariant
                font.pointSize: Appearance.font.size.large

                SequentialAnimation on opacity {
                    running: bluetoothDeviceCardRoot.isPending
                    loops: Animation.Infinite
                    NumberAnimation {
                        from: 1.0
                        to: 0.3
                        duration: 600
                        easing.type: Easing.InOutSine
                    }
                    NumberAnimation {
                        from: 0.3
                        to: 1.0
                        duration: 600
                        easing.type: Easing.InOutSine
                    }
                }
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
                    text: bluetoothDeviceCardRoot.isPending ? (bluetoothDeviceCardRoot.deviceConnected ? "Disconnecting…" : "Connecting…") : bluetoothDeviceCardRoot.deviceConnected ? "Connected" : "Paired"
                    font.pointSize: Appearance.font.size.smaller
                    color: bluetoothDeviceCardRoot.isPending ? Colours.palette.m3tertiary : Colours.palette.m3onSurfaceVariant
                }
            }

            IconButton {
                type: IconButton.Tonal
                icon: bluetoothDeviceCardRoot.isPending ? "hourglass_top" : bluetoothDeviceCardRoot.deviceConnected ? "link_off" : "link"
                font.pointSize: Appearance.font.size.normal
                implicitWidth: 36
                implicitHeight: 36
                focusPolicy: Qt.NoFocus
                enabled: !bluetoothDeviceCardRoot.isPending

                onClicked: bluetoothDeviceCardRoot.toggleConnection()
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
                    profileDescription: AudioProfileDescription.shorten(modelData.description)
                    profileIsActive: modelData.name === bluetoothDeviceCardRoot.associatedCard?.activeProfile

                    onActivated: AudioService.setCardProfile(bluetoothDeviceCardRoot.associatedCard.name, modelData.name)
                }
            }
        }
    }
}
