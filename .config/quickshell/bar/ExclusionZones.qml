import Quickshell
import Quickshell.Wayland
import QtQuick

Item {
    id: exclusionZonesRoot

    required property var screen
    required property int barWidth

    PanelWindow {
        id: leftExclusionWindow

        screen: exclusionZonesRoot.screen

        anchors {
            left: true
            top: true
            bottom: true
        }

        implicitWidth: 1
        implicitHeight: 1

        exclusiveZone: exclusionZonesRoot.barWidth

        WlrLayershell.layer: WlrLayer.Bottom
        WlrLayershell.namespace: "quickshell-bar-exclusion"

        color: "transparent"
        surfaceFormat.opaque: false
        visible: true
    }
}
