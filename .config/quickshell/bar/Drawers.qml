import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Shapes
import "popouts"
import "dashboard"
import "launcher"

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
            property bool dashboardVisible: false
            property bool dashboardHovered: false
            property bool launcherVisible: false
            property bool launcherHovered: false

            readonly property bool hasActivePopout: popoutCurrentName !== ""
            readonly property int shapeJunctionRadius: 36

            property real animatedExtensionWidth: hasActivePopout ? popoutWrapper.popoutWidth : 0
            Behavior on animatedExtensionWidth {
                NumberAnimation { duration: 350; easing.type: Easing.OutCubic }
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

            function toggleDashboard(): void {
                dashboardVisible = !dashboardVisible;
            }

            function toggleLauncher(): void {
                launcherVisible = !launcherVisible;
            }

            function showPopoutByName(name: string): void {
                let positions = barWrapper.barItem.statusIconPositions;
                let iconPos = positions[name];
                let centerY;
                if (iconPos) {
                    let barItem = barWrapper.barItem;
                    let sceneTop = barItem.mapToItem(null, 0, iconPos.top).y;
                    let sceneBottom = barItem.mapToItem(null, 0, iconPos.bottom).y;
                    centerY = (sceneTop + sceneBottom) / 2;
                } else {
                    centerY = drawersWindow.height / 2;
                }
                showPopout(name, centerY);
            }

            function togglePopout(name: string): void {
                if (popoutCurrentName === name) {
                    popoutCurrentName = "";
                    return;
                }
                showPopoutByName(name);
            }

            IpcHandler {
                target: "dashboard"

                function toggle(): void {
                    screenScope.toggleDashboard();
                }
            }

            IpcHandler {
                target: "launcher"

                function toggle(): void {
                    screenScope.toggleLauncher();
                }
            }

            IpcHandler {
                target: "popout"

                function toggle(name: string): void {
                    screenScope.togglePopout(name);
                }

                function show(name: string): void {
                    screenScope.showPopoutByName(name);
                }

                function hide(): void {
                    screenScope.popoutCurrentName = "";
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
                WlrLayershell.keyboardFocus: (screenScope.dashboardVisible || screenScope.launcherVisible) ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

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
                        },
                        Region {
                            x: dashboardWrapper.x
                            y: dashboardWrapper.visible ? dashboardWrapper.y : 0
                            width: dashboardWrapper.visible ? dashboardWrapper.width : 0
                            height: dashboardWrapper.visible ? dashboardWrapper.height : 0
                            intersection: Intersection.Subtract
                        },
                        Region {
                            x: launcherWrapper.x
                            y: launcherWrapper.visible ? launcherWrapper.y : 0
                            width: launcherWrapper.visible ? launcherWrapper.width : 0
                            height: launcherWrapper.visible ? launcherWrapper.height : 0
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
                        dashboardX: dashboardWrapper.x
                        dashboardWidth: dashboardWrapper.visible ? dashboardWrapper.width : 0
                        dashboardHeight: dashboardWrapper.visible ? dashboardWrapper.height : 0
                        launcherX: launcherWrapper.x
                        launcherWidth: launcherWrapper.visible ? launcherWrapper.width : 0
                        launcherHeight: launcherWrapper.visible ? launcherWrapper.height : 0
                    }
                }

                Shape {
                    anchors.fill: parent
                    z: 1
                    preferredRendererType: Shape.CurveRenderer

                    BarInternalBorderShape {
                        barWidth: barTotalWidth
                        barHeight: drawersWindow.height
                        screenWidth: drawersWindow.width
                        junctionRadius: screenScope.shapeJunctionRadius
                        extensionY: popoutWrapper.y
                        extensionHeight: popoutWrapper.hasContent ? popoutWrapper.height : 0
                        extensionWidth: screenScope.animatedExtensionWidth
                        dashboardX: dashboardWrapper.x
                        dashboardWidth: dashboardWrapper.visible ? dashboardWrapper.width : 0
                        dashboardHeight: dashboardWrapper.visible ? dashboardWrapper.height : 0
                        launcherX: launcherWrapper.x
                        launcherWidth: launcherWrapper.visible ? launcherWrapper.width : 0
                        launcherHeight: launcherWrapper.visible ? launcherWrapper.height : 0
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

                MouseArea {
                    id: topStripDashboardHoverTrigger

                    readonly property real topStripHeight: barTotalWidth / 3
                    readonly property real triggerWidth: drawersWindow.width - barTotalWidth * 2

                    x: barTotalWidth + (drawersWindow.width - barTotalWidth - triggerWidth) / 2
                    y: 0
                    z: 3
                    width: triggerWidth
                    height: topStripHeight

                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton

                    onContainsMouseChanged: {
                        if (containsMouse) {
                            dashboardHideTimer.stop();
                            screenScope.dashboardVisible = true;
                        } else if (!screenScope.dashboardHovered) {
                            dashboardHideTimer.restart();
                        }
                    }
                }

                DashboardWrapper {
                    id: dashboardWrapper

                    x: barTotalWidth + (drawersWindow.width - barTotalWidth - width) / 2
                    y: barTotalWidth / 3
                    z: 2

                    dashboardVisible: screenScope.dashboardVisible

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: {
                            screenScope.dashboardHovered = containsMouse;
                            if (containsMouse) {
                                dashboardHideTimer.stop();
                            } else if (!topStripDashboardHoverTrigger.containsMouse) {
                                dashboardHideTimer.restart();
                            }
                        }
                    }
                }


                MouseArea {
                    id: bottomStripLauncherHoverTrigger

                    readonly property real bottomStripHeight: barTotalWidth / 3
                    readonly property real triggerWidth: drawersWindow.width - barTotalWidth * 2

                    x: barTotalWidth + (drawersWindow.width - barTotalWidth - triggerWidth) / 2
                    y: drawersWindow.height - bottomStripHeight
                    z: 3
                    width: triggerWidth
                    height: bottomStripHeight

                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton

                    onContainsMouseChanged: {
                        if (containsMouse) {
                            launcherHideTimer.stop();
                            screenScope.launcherVisible = true;
                        } else if (!screenScope.launcherHovered) {
                            launcherHideTimer.restart();
                        }
                    }
                }

                LauncherWrapper {
                    id: launcherWrapper

                    x: barTotalWidth + (drawersWindow.width - barTotalWidth - width) / 2
                    y: drawersWindow.height - barTotalWidth / 3 - height
                    z: 2

                    launcherVisible: screenScope.launcherVisible

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: {
                            screenScope.launcherHovered = containsMouse;
                            if (containsMouse) {
                                launcherHideTimer.stop();
                            } else if (!bottomStripLauncherHoverTrigger.containsMouse) {
                                launcherHideTimer.restart();
                            }
                        }
                    }
                }

                PopoutWrapper {
                    id: popoutWrapper
                    x: barTotalWidth
                    currentName: screenScope.popoutCurrentName
                    currentCenterY: screenScope.popoutCenterY
                    screenHeight: drawersWindow.height
                    barWidth: barTotalWidth

                    onContainsMouseChanged: {
                        screenScope.popoutHovered = containsMouse;
                        if (!containsMouse) {
                            popoutHideTimer.restart();
                        } else {
                            popoutHideTimer.stop();
                        }
                    }
                }

                MouseArea {
                    id: drawersDismissArea

                    anchors.fill: parent
                    visible: screenScope.dashboardVisible || screenScope.launcherVisible
                    z: 1

                    onClicked: {
                        screenScope.dashboardVisible = false;
                        screenScope.launcherVisible = false;
                    }

                    Keys.onEscapePressed: {
                        screenScope.dashboardVisible = false;
                        screenScope.launcherVisible = false;
                    }
                    focus: screenScope.dashboardVisible || screenScope.launcherVisible
                }

                Timer {
                    id: popoutHideTimer
                    interval: 450
                    onTriggered: {
                        if (!screenScope.popoutHovered && !interactions.isOverBar && !barWrapper.barItem.hasHoveredPopoutIcon) {
                            screenScope.popoutCurrentName = "";
                        }
                    }
                }

                Timer {
                    id: dashboardHideTimer
                    interval: 450
                    onTriggered: {
                        if (!screenScope.dashboardHovered && !topStripDashboardHoverTrigger.containsMouse) {
                            screenScope.dashboardVisible = false;
                        }
                    }
                }

                Timer {
                    id: launcherHideTimer
                    interval: 450
                    onTriggered: {
                        if (!screenScope.launcherHovered && !bottomStripLauncherHoverTrigger.containsMouse) {
                            screenScope.launcherVisible = false;
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
