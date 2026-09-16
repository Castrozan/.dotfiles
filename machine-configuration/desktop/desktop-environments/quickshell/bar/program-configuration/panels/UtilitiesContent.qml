pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import "utilities"
import QtQuick
import QtQuick.Layouts

Item {
    id: utilitiesContentRoot

    implicitWidth: utilitiesToggleGrid.implicitWidth + Appearance.padding.large * 2
    implicitHeight: utilitiesToggleGrid.implicitHeight + Appearance.padding.large * 2

    GridLayout {
        id: utilitiesToggleGrid

        anchors.centerIn: parent
        columns: 3
        rowSpacing: Appearance.spacing.small
        columnSpacing: Appearance.spacing.small

        WifiToggleButton {}

        BluetoothToggleButton {}

        MicrophoneMuteToggleButton {}

        DoNotDisturbToggleButton {}

        KeepAwakeToggleButton {}

        NightLightToggleButton {}
    }
}
