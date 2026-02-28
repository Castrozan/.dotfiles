import Quickshell
import Quickshell.Services.SystemTray
import QtQuick
import ".."

Item {
    id: popoutContentRoot

    required property string currentName

    readonly property bool isTrayMenu: currentName.startsWith("traymenu")
    readonly property int trayMenuIndex: isTrayMenu ? parseInt(currentName.replace("traymenu", "")) : -1
    readonly property var trayMenuHandle: {
        if (!isTrayMenu) return null;
        let items = SystemTray.items.values;
        let idx = trayMenuIndex;
        if (idx >= 0 && idx < items.length) return items[idx].menu;
        return null;
    }

    implicitWidth: 280
    implicitHeight: {
        if (currentName === "network") return networkPopout.implicitHeight + 32;
        if (currentName === "bluetooth") return bluetoothPopout.implicitHeight + 32;
        if (currentName === "battery") return batteryPopout.implicitHeight + 32;

        if (isTrayMenu && trayMenuLoader.item) return trayMenuLoader.item.implicitHeight + 32;
        if (isTrayMenu) return 100;
        return 0;
    }

    NetworkPopout {
        id: networkPopout
        anchors.fill: parent
        visible: popoutContentRoot.currentName === "network"
        active: popoutContentRoot.currentName === "network"

        opacity: visible ? 1 : 0
        Behavior on opacity {
            NumberAnimation { duration: 250 }
        }
    }

    BluetoothPopout {
        id: bluetoothPopout
        anchors.fill: parent
        visible: popoutContentRoot.currentName === "bluetooth"
        active: popoutContentRoot.currentName === "bluetooth"

        opacity: visible ? 1 : 0
        Behavior on opacity {
            NumberAnimation { duration: 250 }
        }
    }

    BatteryPopout {
        id: batteryPopout
        anchors.fill: parent
        visible: popoutContentRoot.currentName === "battery"
        active: popoutContentRoot.currentName === "battery"

        opacity: visible ? 1 : 0
        Behavior on opacity {
            NumberAnimation { duration: 250 }
        }
    }

    Loader {
        id: trayMenuLoader
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        active: popoutContentRoot.isTrayMenu && popoutContentRoot.trayMenuHandle !== null
        visible: active

        sourceComponent: TrayMenuPopout {
            trayMenuHandle: popoutContentRoot.trayMenuHandle
        }

        opacity: visible ? 1 : 0
        Behavior on opacity {
            NumberAnimation { duration: 250 }
        }
    }

    Connections {
        target: popoutContentRoot
        function onCurrentNameChanged() {
            if (popoutContentRoot.isTrayMenu) {
                trayMenuLoader.active = false;
                trayMenuLoader.active = Qt.binding(function() {
                    return popoutContentRoot.isTrayMenu && popoutContentRoot.trayMenuHandle !== null;
                });
            }
        }
    }
}
