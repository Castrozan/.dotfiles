pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

StyledRect {
    id: audioDeviceCardRoot

    signal focusRequested(var item)

    property string deviceName
    property string deviceDescription
    property string devicePortType
    property int deviceVolume: 0
    property bool deviceMuted: false
    property bool deviceIsBluetooth: false
    property bool deviceIsDefault: false
    property bool isOutputDevice: true

    property int pendingVolume: -1
    property real lastClickTimestamp: 0
    readonly property int displayVolume: pendingVolume >= 0 ? pendingVolume : deviceVolume

    onDeviceVolumeChanged: pendingVolume = -1

    function setAsDefault(): void {
        if (isOutputDevice)
            AudioService.setDefaultSink(deviceName);
        else
            AudioService.setDefaultSource(deviceName);
    }

    function adjustVolume(delta: int): void {
        pendingVolume = Math.max(0, Math.min(150, displayVolume + delta));
        if (isOutputDevice)
            AudioService.setSinkVolume(deviceName, pendingVolume);
        else
            AudioService.setSourceVolume(deviceName, pendingVolume);
    }

    color: Colours.tPalette.m3surfaceContainer
    radius: Appearance.rounding.large
    clip: true
    focus: true
    implicitHeight: audioDeviceCardLayout.implicitHeight + Appearance.padding.large * 2
    implicitWidth: 800

    border.width: activeFocus ? 2 : 0
    border.color: Colours.palette.m3primary

    onActiveFocusChanged: {
        if (activeFocus)
            focusRequested(audioDeviceCardRoot);
    }

    StateLayer {
        color: Colours.palette.m3onSurface
        showHoverBackground: true
        function onClicked(): void {
            audioDeviceCardRoot.forceActiveFocus();
            const now = Date.now();
            if (now - audioDeviceCardRoot.lastClickTimestamp < 400) {
                audioDeviceCardRoot.setAsDefault();
                audioDeviceCardRoot.lastClickTimestamp = 0;
            } else {
                audioDeviceCardRoot.lastClickTimestamp = now;
            }
        }
    }

    Keys.onPressed: event => {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            setAsDefault();
            event.accepted = true;
        } else if (event.key === Qt.Key_Space) {
            if (isOutputDevice)
                AudioService.toggleSinkMute(deviceName);
            else
                AudioService.toggleSourceMute(deviceName);
            event.accepted = true;
        } else if (event.key === Qt.Key_Left) {
            adjustVolume(-5);
            event.accepted = true;
        } else if (event.key === Qt.Key_Right) {
            adjustVolume(5);
            event.accepted = true;
        }
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
        width: parent.width * (audioDeviceCardRoot.displayVolume / 150.0)
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

        AudioDeviceDetails {
            deviceDescription: audioDeviceCardRoot.deviceDescription
            devicePortType: audioDeviceCardRoot.devicePortType
            displayVolume: audioDeviceCardRoot.displayVolume
            deviceMuted: audioDeviceCardRoot.deviceMuted
            deviceIsBluetooth: audioDeviceCardRoot.deviceIsBluetooth
            deviceIsDefault: audioDeviceCardRoot.deviceIsDefault
            isOutputDevice: audioDeviceCardRoot.isOutputDevice

            onVolumeRequested: percent => {
                if (audioDeviceCardRoot.isOutputDevice)
                    AudioService.setSinkVolume(audioDeviceCardRoot.deviceName, percent);
                else
                    AudioService.setSourceVolume(audioDeviceCardRoot.deviceName, percent);
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
}
