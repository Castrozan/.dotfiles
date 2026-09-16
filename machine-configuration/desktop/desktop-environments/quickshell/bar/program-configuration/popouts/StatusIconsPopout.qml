import QtQuick.Layouts
import "status-icons"

ColumnLayout {
    id: statusIconsPopoutRoot

    property bool active: false
    spacing: 4

    NotificationSoundRow {
        active: statusIconsPopoutRoot.active
    }

    OutputSoundRow {
        active: statusIconsPopoutRoot.active
    }

    MicrophoneRow {
        active: statusIconsPopoutRoot.active
    }

    KeyboardBacklightRow {
        active: statusIconsPopoutRoot.active
    }

    NetworkRow {
        active: statusIconsPopoutRoot.active
    }

    BluetoothRow {
        active: statusIconsPopoutRoot.active
    }

    BatteryRow {
        active: statusIconsPopoutRoot.active
    }
}
