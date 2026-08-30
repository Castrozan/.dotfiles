import QtQuick
import QtQuick.Layouts
import "./status-icons/"

ColumnLayout {
    id: statusIconsModuleRoot

    required property var barRoot
    required property var screenScope

    readonly property bool hasHoveredPopoutIcon: networkIcon.isHovered || bluetoothIcon.isHovered || (batteryIcon.visible && batteryIcon.isHovered)

    spacing: 2

    Component.onCompleted: _registerAllIconPositions()
    onYChanged: _registerAllIconPositions()
    onHeightChanged: _registerAllIconPositions()

    function _registerAllIconPositions(): void {
        _registerIconPosition(vpnIcon, "");
        _registerIconPosition(notificationSoundIcon, "");
        _registerIconPosition(outputDeviceTypeIcon, "");
        _registerIconPosition(microphoneIcon, "");
        if (keyboardBacklightIcon.visible)
            _registerIconPosition(keyboardBacklightIcon, "");
        _registerIconPosition(networkIcon, "network");
        _registerIconPosition(bluetoothIcon, "bluetooth");
        if (batteryIcon.visible)
            _registerIconPosition(batteryIcon, "battery");
    }

    function _registerIconPosition(iconItem: var, popoutName: string): void {
        if (!barRoot || !iconItem) return;
        let globalPos = iconItem.mapToItem(barRoot, 0, 0);
        barRoot.registerStatusIconPosition(popoutName, globalPos.y, globalPos.y + iconItem.height);
    }

    VpnStatusIcon {
        id: vpnIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        Layout.topMargin: 4
    }

    NotificationSoundStatusIcon {
        id: notificationSoundIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
    }

    OutputDeviceStatusIcon {
        id: outputDeviceTypeIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
    }

    MicrophoneStatusIcon {
        id: microphoneIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
    }

    NetworkStatusIcon {
        id: networkIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        screenScope: statusIconsModuleRoot.screenScope
    }

    BluetoothStatusIcon {
        id: bluetoothIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        screenScope: statusIconsModuleRoot.screenScope
    }

    KeyboardBacklightStatusIcon {
        id: keyboardBacklightIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
    }

    BatteryStatusIcon {
        id: batteryIcon
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: 28
        Layout.preferredHeight: 28
        screenScope: statusIconsModuleRoot.screenScope
    }
}
