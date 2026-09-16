pragma ComponentBehavior: Bound

import Quickshell
import Quickshell.Wayland
import QtQuick

PanelWindow {
    id: switcherPanel

    required property var windowList
    required property int selectedIndex
    required property color accentColor
    required property color backgroundColor
    required property color foregroundColor

    signal cancelRequested
    signal windowSelected(int index)

    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }

    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "quickshell-switcher"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

    color: "transparent"
    surfaceFormat.opaque: false

    MouseArea {
        anchors.fill: parent
        onClicked: switcherPanel.cancelRequested()
    }

    Item {
        anchors.centerIn: parent

        width: windowListRow.width
        height: windowListRow.height

        Row {
            id: windowListRow
            spacing: 16

            Repeater {
                model: switcherPanel.windowList

                WindowThumbnailCard {
                    id: windowCard
                    required property var modelData
                    required property int index

                    toplevelHandle: windowCard.modelData.waylandHandle
                    windowTitle: windowCard.modelData.title
                    windowClass: windowCard.modelData.windowClass
                    isSelected: windowCard.index === switcherPanel.selectedIndex
                    accentColor: switcherPanel.accentColor
                    backgroundColor: switcherPanel.backgroundColor
                    foregroundColor: switcherPanel.foregroundColor

                    onClicked: {
                        switcherPanel.windowSelected(windowCard.index);
                    }
                }
            }
        }
    }
}
