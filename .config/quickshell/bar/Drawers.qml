import Quickshell
import Quickshell.Wayland
import QtQuick
import "popouts"

Scope {
    id: drawersRoot

    Variants {
        model: Quickshell.screens

        Scope {
            id: screenScope

            required property var modelData
            property var screen: modelData

            readonly property int barContentWidth: 48
            readonly property int barTotalWidth: barContentWidth

            property string popoutCurrentName: ""
            property real popoutCenterY: 0
            property bool popoutHovered: false

            readonly property bool hasActivePopout: popoutCurrentName !== ""
            readonly property int junctionCornerSize: 36

            function showPopout(name: string, centerY: real): void {
                popoutCurrentName = name;
                popoutCenterY = centerY;
            }

            function hidePopout(): void {
                if (!popoutHovered && !barWrapper.barItem.hasHoveredPopoutIcon) {
                    popoutHideTimer.restart();
                }
            }

            PanelWindow {
                id: drawersWindow

                screen: screenScope.screen

                anchors {
                    top: true
                    bottom: true
                    left: true
                    right: true
                }

                exclusionMode: ExclusionMode.Ignore
                WlrLayershell.layer: WlrLayer.Top
                WlrLayershell.namespace: "quickshell-bar"
                WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

                color: "transparent"
                surfaceFormat.opaque: false

                mask: Region {
                    x: barTotalWidth
                    y: 0
                    width: drawersWindow.width - barTotalWidth
                    height: drawersWindow.height
                    intersection: Intersection.Xor

                    regions: [
                        Region {
                            x: popoutWrapper.x
                            y: popoutWrapper.visible ? popoutWrapper.y - screenScope.junctionCornerSize : 0
                            width: popoutWrapper.visible ? popoutWrapper.width : 0
                            height: popoutWrapper.visible ? popoutWrapper.height + screenScope.junctionCornerSize * 2 : 0
                            intersection: Intersection.Subtract
                        }
                    ]
                }

                Interactions {
                    id: interactions
                    anchors.fill: parent
                    barWidth: barTotalWidth
                    barComponent: barWrapper.barItem

                    onPopoutAreaLeft: {
                        if (!popoutHovered && !barWrapper.barItem.hasHoveredPopoutIcon) {
                            popoutHideTimer.restart();
                        }
                    }
                }

                BarWrapper {
                    id: barWrapper
                    width: barTotalWidth
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left

                    screenScope: screenScope
                }

                PopoutWrapper {
                    id: popoutWrapper
                    x: barTotalWidth
                    currentName: screenScope.popoutCurrentName
                    currentCenterY: screenScope.popoutCenterY
                    screenHeight: drawersWindow.height

                    onContainsMouseChanged: {
                        screenScope.popoutHovered = containsMouse;
                        if (!containsMouse) {
                            popoutHideTimer.restart();
                        } else {
                            popoutHideTimer.stop();
                        }
                    }
                }

                Rectangle {
                    id: barRightBorderAbovePopout
                    x: barTotalWidth - 1
                    y: 0
                    width: 1
                    height: popoutWrapper.visible ? Math.max(0, popoutWrapper.y - screenScope.junctionCornerSize) : drawersWindow.height
                    color: ThemeColors.primary
                    z: 10
                }

                Rectangle {
                    id: barRightBorderBelowPopout
                    visible: popoutWrapper.visible
                    x: barTotalWidth - 1
                    y: popoutWrapper.y + popoutWrapper.height + screenScope.junctionCornerSize
                    width: 1
                    height: Math.max(0, drawersWindow.height - (popoutWrapper.y + popoutWrapper.height + screenScope.junctionCornerSize))
                    color: ThemeColors.primary
                    z: 10
                }

                Item {
                    id: topJunctionConcaveCorner
                    visible: popoutWrapper.visible
                    x: barTotalWidth - 1
                    y: popoutWrapper.y - screenScope.junctionCornerSize
                    width: screenScope.junctionCornerSize + 1
                    height: screenScope.junctionCornerSize + 1
                    clip: true
                    z: 10

                    Rectangle {
                        x: 0
                        y: -screenScope.junctionCornerSize
                        width: screenScope.junctionCornerSize * 2
                        height: screenScope.junctionCornerSize * 2
                        radius: screenScope.junctionCornerSize
                        color: ThemeColors.background
                        border.color: ThemeColors.primary
                        border.width: 1
                    }
                }

                Item {
                    id: bottomJunctionConcaveCorner
                    visible: popoutWrapper.visible
                    x: barTotalWidth - 1
                    y: popoutWrapper.y + popoutWrapper.height
                    width: screenScope.junctionCornerSize + 1
                    height: screenScope.junctionCornerSize + 1
                    clip: true
                    z: 10

                    Rectangle {
                        x: 0
                        y: 0
                        width: screenScope.junctionCornerSize * 2
                        height: screenScope.junctionCornerSize * 2
                        radius: screenScope.junctionCornerSize
                        color: ThemeColors.background
                        border.color: ThemeColors.primary
                        border.width: 1
                    }
                }

                Timer {
                    id: popoutHideTimer
                    interval: 300
                    onTriggered: {
                        if (!screenScope.popoutHovered && !interactions.isOverBar && !barWrapper.barItem.hasHoveredPopoutIcon) {
                            screenScope.popoutCurrentName = "";
                        }
                    }
                }
            }

            ExclusionZones {
                screen: screenScope.screen
                barWidth: barTotalWidth
            }
        }
    }
}
