import Quickshell
import Quickshell.Wayland
import QtQuick

Item {
    id: exclusionZonesRoot

    required property var screen
    required property int barWidth

    readonly property int stripThickness: barWidth / 3

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

    PanelWindow {
        id: topExclusionWindow

        screen: exclusionZonesRoot.screen

        anchors {
            top: true
            left: true
            right: true
        }

        implicitWidth: 1
        implicitHeight: 1

        exclusiveZone: exclusionZonesRoot.stripThickness

        WlrLayershell.layer: WlrLayer.Bottom
        WlrLayershell.namespace: "quickshell-bar-exclusion-top"

        color: "transparent"
        surfaceFormat.opaque: false
        visible: true
    }

    PanelWindow {
        id: bottomExclusionWindow

        screen: exclusionZonesRoot.screen

        anchors {
            bottom: true
            left: true
            right: true
        }

        implicitWidth: 1
        implicitHeight: 1

        exclusiveZone: exclusionZonesRoot.stripThickness

        WlrLayershell.layer: WlrLayer.Bottom
        WlrLayershell.namespace: "quickshell-bar-exclusion-bottom"

        color: "transparent"
        surfaceFormat.opaque: false
        visible: true
    }

    PanelWindow {
        id: rightExclusionWindow

        screen: exclusionZonesRoot.screen

        anchors {
            right: true
            top: true
            bottom: true
        }

        implicitWidth: 1
        implicitHeight: 1

        exclusiveZone: exclusionZonesRoot.stripThickness

        WlrLayershell.layer: WlrLayer.Bottom
        WlrLayershell.namespace: "quickshell-bar-exclusion-right"

        color: "transparent"
        surfaceFormat.opaque: false
        visible: true
    }
}
