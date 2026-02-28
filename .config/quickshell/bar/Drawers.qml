import Quickshell
import Quickshell.Wayland
import QtQuick
import QtQuick.Shapes
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
            readonly property int shapeJunctionRadius: 36

            property real animatedExtensionWidth: hasActivePopout ? popoutWrapper.popoutWidth : 0
            Behavior on animatedExtensionWidth {
                NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
            }

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
                            x: barTotalWidth
                            y: 0
                            width: drawersWindow.width - barTotalWidth
                            height: barTotalWidth / 3
                            intersection: Intersection.Subtract
                        },
                        Region {
                            x: barTotalWidth
                            y: drawersWindow.height - barTotalWidth / 3
                            width: drawersWindow.width - barTotalWidth
                            height: barTotalWidth / 3
                            intersection: Intersection.Subtract
                        },
                        Region {
                            x: drawersWindow.width - barTotalWidth / 3
                            y: barTotalWidth / 3
                            width: barTotalWidth / 3
                            height: drawersWindow.height - barTotalWidth * 2 / 3
                            intersection: Intersection.Subtract
                        },
                        Region {
                            x: popoutWrapper.x
                            y: popoutWrapper.visible ? popoutWrapper.y - screenScope.shapeJunctionRadius : 0
                            width: popoutWrapper.visible ? popoutWrapper.width : 0
                            height: popoutWrapper.visible ? popoutWrapper.height + screenScope.shapeJunctionRadius * 2 : 0
                            intersection: Intersection.Subtract
                        }
                    ]
                }

                Shape {
                    id: barBackgroundShape
                    anchors.fill: parent
                    z: 0
                    preferredRendererType: Shape.CurveRenderer

                    BarBackgroundShape {
                        barWidth: barTotalWidth
                        barHeight: drawersWindow.height
                        screenWidth: drawersWindow.width
                        junctionRadius: screenScope.shapeJunctionRadius
                        extensionY: popoutWrapper.y
                        extensionHeight: popoutWrapper.hasContent ? popoutWrapper.height : 0
                        extensionWidth: screenScope.animatedExtensionWidth
                    }
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
