pragma ComponentBehavior: Bound

import "../../components"
import "../.."
import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: audioDeviceDetailsRoot

    required property string deviceDescription
    required property string devicePortType
    required property int displayVolume
    required property bool deviceMuted
    required property bool deviceIsBluetooth
    required property bool deviceIsDefault
    required property bool isOutputDevice

    signal volumeRequested(int percent)

    Layout.fillWidth: true
    spacing: Appearance.spacing.smaller

    RowLayout {
        Layout.fillWidth: true
        spacing: Appearance.spacing.small

        StyledText {
            Layout.fillWidth: true
            text: audioDeviceDetailsRoot.deviceDescription
            font.pointSize: Appearance.font.size.normal
            font.weight: audioDeviceDetailsRoot.deviceIsDefault ? Font.Medium : Font.Normal
            color: audioDeviceDetailsRoot.deviceIsDefault ? Colours.palette.m3primary : Colours.palette.m3onSurface
            elide: Text.ElideRight
        }

        StyledText {
            text: audioDeviceDetailsRoot.displayVolume + "%"
            font.pointSize: Appearance.font.size.small
            font.weight: Font.Medium
            color: audioDeviceDetailsRoot.deviceMuted ? Colours.palette.m3error : audioDeviceDetailsRoot.displayVolume > 100 ? Colours.palette.m3error : Colours.palette.m3onSurfaceVariant
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Appearance.spacing.small

        MaterialIcon {
            text: audioDeviceDetailsRoot.deviceIsBluetooth ? "bluetooth" : audioDeviceDetailsRoot.devicePortType.toLowerCase() === "headset" ? "headphones" : audioDeviceDetailsRoot.isOutputDevice ? "speaker" : "settings_voice"
            font.pointSize: Appearance.font.size.small
            color: Colours.palette.m3onSurfaceVariant
        }

        StyledText {
            text: {
                if (audioDeviceDetailsRoot.deviceIsBluetooth)
                    return "Bluetooth";
                if (audioDeviceDetailsRoot.devicePortType)
                    return audioDeviceDetailsRoot.devicePortType;
                return audioDeviceDetailsRoot.isOutputDevice ? "Output" : "Input";
            }
            font.pointSize: Appearance.font.size.smaller
            color: Colours.palette.m3onSurfaceVariant
        }

        Item {
            Layout.fillWidth: true
        }

        StyledText {
            text: audioDeviceDetailsRoot.deviceIsDefault ? "Default" : ""
            font.pointSize: Appearance.font.size.smaller
            font.weight: Font.Medium
            color: Colours.palette.m3primary
            visible: audioDeviceDetailsRoot.deviceIsDefault
        }
    }

    StyledSlider {
        Layout.fillWidth: true
        implicitHeight: Appearance.padding.normal * 2.5
        from: 0
        to: 1.5
        value: audioDeviceDetailsRoot.displayVolume / 100.0
        focusPolicy: Qt.NoFocus

        onMoved: {
            const percent = Math.round(value * 100);
            audioDeviceDetailsRoot.volumeRequested(percent);
        }
    }
}
