import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Shapes
import "popouts"
import "dashboard"
import "launcher"
import "panels"

Scope {
    id: drawersRoot

    signal osdSocketMessageReceived(string message)
    signal hyprlandFullscreenEventReceived()

    Connections {
        target: HyprlandEventsService
        function onFullscreenChanged() {
            drawersRoot.hyprlandFullscreenEventReceived();
        }
    }

    SocketServer {
        active: true
        path: Quickshell.env("XDG_RUNTIME_DIR") + "/quickshell-osd.sock"

        handler: Socket {
            parser: SplitParser {
                splitMarker: "\n"
                onRead: message => drawersRoot.osdSocketMessageReceived(message)
            }
        }
    }

    Variants {
        model: Quickshell.screens

        Scope {
            id: screenScope

            required property var modelData
            property var screen: modelData

            readonly property int barContentWidth: 48
            readonly property int barTotalWidth: barContentWidth

            property bool activeWorkspaceHasFullscreenWindow: false

            Process {
                id: activeWorkspaceFullscreenQueryProcess
                command: ["hyprctl", "clients", "-j"]
                stdout: SplitParser {
                    splitMarker: ""
                    onRead: data => {
                        try {
                            let clients = JSON.parse(data);
                            let wsId = Hyprland.focusedWorkspace ? Hyprland.focusedWorkspace.id : -1;
                            screenScope.activeWorkspaceHasFullscreenWindow = clients.some(c => c.workspace.id === wsId && c.fullscreen === 2);
                        } catch (e) {
                            screenScope.activeWorkspaceHasFullscreenWindow = false;
                        }
                    }
                }
            }

            Component.onCompleted: activeWorkspaceFullscreenQueryProcess.running = true

            Connections {
                target: Hyprland
                function onFocusedWorkspaceChanged() {
                    activeWorkspaceFullscreenQueryProcess.running = true;
                }
            }

            Connections {
                target: drawersRoot
                function onHyprlandFullscreenEventReceived() {
                    activeWorkspaceFullscreenQueryProcess.running = true;
                }
            }
            readonly property int shapeJunctionRadius: 36

            property real animatedExtensionWidth: screenDrawerState.hasActivePopout ? popoutWrapper.popoutWidth : 0
            Behavior on animatedExtensionWidth {
                NumberAnimation { duration: 350; easing.type: Easing.OutCubic }
            }

            QtObject {
                id: popoutIconAnchors

                function centerYForPopout(name: string): real {
                    let iconPosition = barWrapper.barItem.statusIconPositions[name];
                    if (!iconPosition)
                        return drawersWindow.height / 2;
                    let sceneTop = barWrapper.barItem.mapToItem(null, 0, iconPosition.top).y;
                    let sceneBottom = barWrapper.barItem.mapToItem(null, 0, iconPosition.bottom).y;
                    return (sceneTop + sceneBottom) / 2;
                }
            }

            DrawerState {
                id: screenDrawerState

                popoutAnchorResolver: popoutIconAnchors
                popoutIconHovered: barWrapper.barItem.hasHoveredPopoutIcon
            }

            DrawerHoverController {
                id: screenHoverController

                drawerState: screenDrawerState
                pointerOverBar: interactions.isOverBar
            }

            DrawerIpcAdapter {
                drawerState: screenDrawerState
                drawerHoverController: screenHoverController
            }

            Connections {
                target: drawersRoot
                function onOsdSocketMessageReceived(message: string): void {
                    osdWrapper.handleOsdMessage(message);
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
                WlrLayershell.layer: screenScope.activeWorkspaceHasFullscreenWindow ? WlrLayer.Background : WlrLayer.Top
                WlrLayershell.namespace: "quickshell-bar"
                WlrLayershell.keyboardFocus: screenDrawerState.hasAnyPanelVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

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
                        },
                        Region {
                            x: sessionWrapper.visible ? sessionWrapper.x : 0
                            y: sessionWrapper.visible ? sessionWrapper.y : 0
                            width: sessionWrapper.visible ? sessionWrapper.width : 0
                            height: sessionWrapper.visible ? sessionWrapper.height : 0
                            intersection: Intersection.Subtract
                        },
                        Region {
                            x: utilitiesWrapper.visible ? utilitiesWrapper.x : 0
                            y: utilitiesWrapper.visible ? utilitiesWrapper.y : 0
                            width: utilitiesWrapper.visible ? utilitiesWrapper.width : 0
                            height: utilitiesWrapper.visible ? utilitiesWrapper.height : 0
                            intersection: Intersection.Subtract
                        },
                        Region {
                            x: osdWrapper.visible ? osdWrapper.x : 0
                            y: osdWrapper.visible ? osdWrapper.y : 0
                            width: osdWrapper.visible ? osdWrapper.width : 0
                            height: osdWrapper.visible ? osdWrapper.height : 0
                            intersection: Intersection.Subtract
                        },
                        Region {
                            x: sidebarWrapper.visible ? sidebarWrapper.x : 0
                            y: sidebarWrapper.visible ? sidebarWrapper.y : 0
                            width: sidebarWrapper.visible ? sidebarWrapper.width : 0
                            height: sidebarWrapper.visible ? sidebarWrapper.height : 0
                            intersection: Intersection.Subtract
                        }
                    ]
                }

                QtObject {
                    id: aggregatedRightPanelGeometry

                    readonly property bool hasSession: sessionWrapper.visible && sessionWrapper.width > 0
                    readonly property bool hasSidebar: sidebarWrapper.visible && sidebarWrapper.width > 0
                    readonly property bool hasUtilities: utilitiesWrapper.visible && utilitiesWrapper.height > 0
                    readonly property bool hasOsd: osdWrapper.visible && osdWrapper.width > 0
                    readonly property bool hasAnyRightPanel: hasSession || hasSidebar || hasUtilities || hasOsd

                    readonly property real sessionTop: hasSession ? sessionWrapper.y : 99999
                    readonly property real sessionBottom: hasSession ? sessionWrapper.y + sessionWrapper.height : 0
                    readonly property real sidebarTop: hasSidebar ? sidebarWrapper.y : 99999
                    readonly property real sidebarBottom: hasSidebar ? sidebarWrapper.y + sidebarWrapper.height : 0
                    readonly property real utilitiesTop: hasUtilities ? utilitiesWrapper.y : 99999
                    readonly property real utilitiesBottom: hasUtilities ? utilitiesWrapper.y + utilitiesWrapper.height : 0
                    readonly property real osdTop: hasOsd ? osdWrapper.y : 99999
                    readonly property real osdBottom: hasOsd ? osdWrapper.y + osdWrapper.height : 0

                    readonly property real aggregatedY: hasAnyRightPanel ? Math.min(sessionTop, sidebarTop, utilitiesTop, osdTop) : 0
                    readonly property real aggregatedBottom: hasAnyRightPanel ? Math.max(sessionBottom, sidebarBottom, utilitiesBottom, osdBottom) : 0
                    readonly property real aggregatedHeight: hasAnyRightPanel ? aggregatedBottom - aggregatedY : 0
                    readonly property real aggregatedWidth: hasAnyRightPanel ? Math.max(
                        hasSession ? sessionWrapper.width + sidebarWrapper.width : 0,
                        hasSidebar ? sidebarWrapper.width : 0,
                        hasUtilities ? utilitiesWrapper.width : 0,
                        hasOsd ? osdWrapper.width + (hasSession ? sessionWrapper.width : 0) + (hasSidebar ? sidebarWrapper.width : 0) : 0
                    ) : 0
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
                        rightPanelY: aggregatedRightPanelGeometry.aggregatedY
                        rightPanelWidth: aggregatedRightPanelGeometry.aggregatedWidth
                        rightPanelHeight: aggregatedRightPanelGeometry.aggregatedHeight
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
                        rightPanelY: aggregatedRightPanelGeometry.aggregatedY
                        rightPanelWidth: aggregatedRightPanelGeometry.aggregatedWidth
                        rightPanelHeight: aggregatedRightPanelGeometry.aggregatedHeight
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

                    onPopoutAreaLeft: screenDrawerState.hidePopout()
                }

                BarWrapper {
                    id: barWrapper
                    width: barTotalWidth
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left

                    screenScope: screenDrawerState
                }

                MouseArea {
                    id: topStripDashboardHoverTrigger

                    readonly property real topStripHeight: 2
                    readonly property real triggerWidth: drawersWindow.width - barTotalWidth * 2

                    x: barTotalWidth + (drawersWindow.width - barTotalWidth - triggerWidth) / 2
                    y: 0
                    z: 3
                    width: triggerWidth
                    height: topStripHeight

                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton

                    onContainsMouseChanged: containsMouse ? screenHoverController.dashboard.triggerEntered() : screenHoverController.dashboard.triggerLeft()
                }

                DashboardWrapper {
                    id: dashboardWrapper

                    x: barTotalWidth + (drawersWindow.width - barTotalWidth - width) / 2
                    y: barTotalWidth / 3
                    z: 2

                    dashboardVisible: screenDrawerState.dashboardVisible

                    onCloseRequested: screenDrawerState.closeDashboard()

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: containsMouse ? screenHoverController.dashboard.contentEntered() : screenHoverController.dashboard.contentLeft()
                    }
                }


                MouseArea {
                    id: bottomStripLauncherHoverTrigger

                    readonly property real bottomStripHeight: 2
                    readonly property real triggerWidth: drawersWindow.width - barTotalWidth * 2

                    x: barTotalWidth + (drawersWindow.width - barTotalWidth - triggerWidth) / 2
                    y: drawersWindow.height - bottomStripHeight
                    z: 3
                    width: triggerWidth
                    height: bottomStripHeight

                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton

                    onContainsMouseChanged: containsMouse ? screenHoverController.launcher.triggerEntered() : screenHoverController.launcher.triggerLeft()
                }

                LauncherWrapper {
                    id: launcherWrapper

                    x: barTotalWidth + (drawersWindow.width - barTotalWidth - width) / 2
                    y: drawersWindow.height - barTotalWidth / 3 - height
                    z: 2

                    launcherVisible: screenDrawerState.launcherVisible

                    onLauncherCloseRequested: screenDrawerState.closeLauncher()
                    Keys.onEscapePressed: screenDrawerState.closeLauncher()

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: containsMouse ? screenHoverController.launcher.contentEntered() : screenHoverController.launcher.contentLeft()
                    }
                }

                SessionWrapper {
                    id: sessionWrapper

                    x: drawersWindow.width - barTotalWidth / 3 - sidebarWrapper.width - width
                    y: (drawersWindow.height - height) / 2
                    z: 2

                    sessionVisible: screenDrawerState.sessionVisible

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: containsMouse ? screenHoverController.session.contentEntered() : screenHoverController.session.contentLeft()
                    }
                }

                MouseArea {
                    id: rightStripSidebarHoverTrigger

                    readonly property real rightStripWidth: barTotalWidth / 3
                    readonly property real rightStripInnerTop: barTotalWidth / 3
                    readonly property real rightStripInnerHeight: drawersWindow.height - barTotalWidth * 2 / 3
                    readonly property real zoneHeight: rightStripInnerHeight / 3

                    x: drawersWindow.width - rightStripWidth
                    y: rightStripInnerTop
                    z: 3
                    width: rightStripWidth
                    height: zoneHeight

                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton

                    onContainsMouseChanged: containsMouse ? screenHoverController.sidebar.triggerEntered() : screenHoverController.sidebar.triggerLeft()
                }

                MouseArea {
                    id: rightStripOsdHoverTrigger

                    x: drawersWindow.width - rightStripSidebarHoverTrigger.rightStripWidth
                    y: rightStripSidebarHoverTrigger.rightStripInnerTop + rightStripSidebarHoverTrigger.zoneHeight
                    z: 3
                    width: rightStripSidebarHoverTrigger.rightStripWidth
                    height: rightStripSidebarHoverTrigger.zoneHeight

                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton

                    onContainsMouseChanged: containsMouse ? screenHoverController.osd.triggerEntered() : screenHoverController.osd.triggerLeft()
                }

                MouseArea {
                    id: rightStripSessionHoverTrigger

                    x: drawersWindow.width - rightStripSidebarHoverTrigger.rightStripWidth
                    y: rightStripSidebarHoverTrigger.rightStripInnerTop + rightStripSidebarHoverTrigger.zoneHeight * 2
                    z: 3
                    width: rightStripSidebarHoverTrigger.rightStripWidth
                    height: rightStripSidebarHoverTrigger.zoneHeight

                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton

                    onContainsMouseChanged: containsMouse ? screenHoverController.session.triggerEntered() : screenHoverController.session.triggerLeft()
                }

                UtilitiesWrapper {
                    id: utilitiesWrapper

                    x: drawersWindow.width - barTotalWidth / 3 - width
                    y: drawersWindow.height - barTotalWidth / 3 - height
                    z: 3

                    utilitiesVisible: screenDrawerState.utilitiesVisible

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: containsMouse ? screenHoverController.utilities.contentEntered() : screenHoverController.utilities.contentLeft()
                    }
                }

                SidebarWrapper {
                    id: sidebarWrapper

                    readonly property real sidebarTopEdge: barTotalWidth / 3
                    readonly property real sidebarBottomEdge: drawersWindow.height - barTotalWidth / 3

                    x: drawersWindow.width - barTotalWidth / 3 - width
                    y: sidebarTopEdge
                    z: 2
                    height: sidebarBottomEdge - sidebarTopEdge

                    sidebarVisible: screenDrawerState.sidebarVisible
                    contentAvailableHeight: sidebarBottomEdge - sidebarTopEdge - utilitiesWrapper.height

                    onCloseRequested: screenDrawerState.closeSidebar()

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: containsMouse ? screenHoverController.sidebar.contentEntered() : screenHoverController.sidebar.contentLeft()
                    }
                }

                OsdWrapper {
                    id: osdWrapper

                    x: drawersWindow.width - barTotalWidth / 3 - sidebarWrapper.width - sessionWrapper.width - width
                    y: (drawersWindow.height - height) / 2
                    z: 2

                    osdVisible: screenDrawerState.osdVisible

                    onOsdMessageReceived: screenHoverController.showOsdTemporarily()

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: containsMouse ? screenHoverController.osd.contentEntered() : screenHoverController.osd.contentLeft()
                    }
                }

                PopoutWrapper {
                    id: popoutWrapper
                    x: barTotalWidth
                    currentName: screenDrawerState.popoutCurrentName
                    currentCenterY: screenDrawerState.popoutCenterY
                    screenHeight: drawersWindow.height
                    barWidth: barTotalWidth

                    onContainsMouseChanged: containsMouse ? screenHoverController.popoutContentEntered() : screenHoverController.popoutContentLeft()
                }

                MouseArea {
                    id: drawersDismissArea

                    anchors.fill: parent
                    visible: screenDrawerState.hasAnyPanelVisible
                    z: 1

                    onClicked: screenDrawerState.closeAllPanels()

                    Keys.onEscapePressed: screenDrawerState.closeAllPanels()
                    focus: (screenDrawerState.launcherVisible || screenDrawerState.sessionVisible || screenDrawerState.utilitiesVisible) && !screenDrawerState.sidebarVisible && !screenDrawerState.dashboardVisible
                }
            }

            WallpaperTransitionOverlay {
                screen: screenScope.screen
            }

            ExclusionZones {
                screen: screenScope.screen
                barWidth: barTotalWidth
            }
        }
    }
}
