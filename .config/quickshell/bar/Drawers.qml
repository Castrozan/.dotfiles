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
    signal hyprlandWindowLayoutEventReceived()

    readonly property string hyprlandSocket2Path: Quickshell.env("XDG_RUNTIME_DIR") + "/hypr/" + Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE") + "/.socket2.sock"

    Process {
        id: hyprlandEventMonitorProcess
        command: ["nc", "-U", drawersRoot.hyprlandSocket2Path]
        running: true
        stdout: SplitParser {
            splitMarker: "\n"
            onRead: data => {
                if (data.startsWith("fullscreen>>")) {
                    drawersRoot.hyprlandFullscreenEventReceived();
                } else if (data.startsWith("openwindow>>") || data.startsWith("closewindow>>") || data.startsWith("movewindow>>")) {
                    drawersRoot.hyprlandWindowLayoutEventReceived();
                }
            }
        }
        onExited: running = true
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

            property string popoutCurrentName: ""
            property real popoutCenterY: 0
            property bool popoutHovered: false
            property bool dashboardVisible: false
            property bool dashboardHovered: false
            property bool launcherVisible: false
            property bool launcherHovered: false
            property bool sessionVisible: false
            property bool sessionHovered: false
            property bool utilitiesVisible: false
            property bool utilitiesHovered: false
            property bool osdVisible: false
            property bool sidebarVisible: false
            property bool sidebarHovered: false

            property bool activeWorkspaceHasFullscreenWindow: false
            readonly property bool hasActivePopout: popoutCurrentName !== ""

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


            function toggleSession(): void {
                sessionVisible = !sessionVisible;
            }

            function toggleUtilities(): void {
                utilitiesVisible = !utilitiesVisible;
            }

            function toggleSidebar(): void {
                sidebarVisible = !sidebarVisible;
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
                target: "session"

                function toggle(): void {
                    screenScope.toggleSession();
                }
            }

            IpcHandler {
                target: "utilities"

                function toggle(): void {
                    screenScope.toggleUtilities();
                }
            }

            IpcHandler {
                target: "sidebar"

                function toggle(): void {
                    screenScope.toggleSidebar();
                }
            }

            IpcHandler {
                target: "osd"

                function show(): void {
                    screenScope.osdVisible = true;
                    osdAutoHideTimer.restart();
                }

                function hide(): void {
                    screenScope.osdVisible = false;
                }
            }

            Connections {
                target: drawersRoot
                function onOsdSocketMessageReceived(message: string): void {
                    osdWrapper.handleOsdMessage(message);
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
                WlrLayershell.layer: screenScope.activeWorkspaceHasFullscreenWindow ? WlrLayer.Background : WlrLayer.Top
                WlrLayershell.namespace: "quickshell-bar"
                WlrLayershell.keyboardFocus: (screenScope.dashboardVisible || screenScope.launcherVisible || screenScope.sessionVisible || screenScope.utilitiesVisible || screenScope.sidebarVisible) ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

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

                    readonly property real topStripHeight: 2
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
                            dashboardShowDelayTimer.restart();
                        } else {
                            dashboardShowDelayTimer.stop();
                            if (!screenScope.dashboardHovered)
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

                    readonly property real bottomStripHeight: 2
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

                    onLauncherCloseRequested: screenScope.launcherVisible = false
                    Keys.onEscapePressed: screenScope.launcherVisible = false

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

                SessionWrapper {
                    id: sessionWrapper

                    x: drawersWindow.width - barTotalWidth / 3 - sidebarWrapper.width - width
                    y: (drawersWindow.height - height) / 2
                    z: 2

                    sessionVisible: screenScope.sessionVisible

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: {
                            screenScope.sessionHovered = containsMouse;
                            if (containsMouse) {
                                sessionHideTimer.stop();
                            } else if (!rightStripSessionHoverTrigger.containsMouse) {
                                sessionHideTimer.restart();
                            }
                        }
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

                    onContainsMouseChanged: {
                        if (containsMouse) {
                            sidebarHideTimer.stop();
                            sidebarShowDelayTimer.restart();
                        } else {
                            sidebarShowDelayTimer.stop();
                            if (!screenScope.sidebarHovered)
                                sidebarHideTimer.restart();
                        }
                    }
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

                    property bool osdHovered: false

                    onContainsMouseChanged: {
                        if (containsMouse) {
                            osdHideTimer.stop();
                            osdShowDelayTimer.restart();
                        } else {
                            osdShowDelayTimer.stop();
                            if (!osdHovered)
                                osdHideTimer.restart();
                        }
                    }
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

                    onContainsMouseChanged: {
                        if (containsMouse) {
                            sessionHideTimer.stop();
                            sessionShowDelayTimer.restart();
                        } else {
                            sessionShowDelayTimer.stop();
                            if (!screenScope.sessionHovered)
                                sessionHideTimer.restart();
                        }
                    }
                }

                UtilitiesWrapper {
                    id: utilitiesWrapper

                    x: drawersWindow.width - barTotalWidth / 3 - width
                    y: drawersWindow.height - barTotalWidth / 3 - height
                    z: 3

                    utilitiesVisible: screenScope.utilitiesVisible

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: {
                            screenScope.utilitiesHovered = containsMouse;
                            if (containsMouse) {
                                utilitiesHideTimer.stop();
                            } else {
                                utilitiesHideTimer.restart();
                            }
                        }
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

                    sidebarVisible: screenScope.sidebarVisible
                    contentAvailableHeight: sidebarBottomEdge - sidebarTopEdge - utilitiesWrapper.height

                    onCloseRequested: screenScope.sidebarVisible = false

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: {
                            screenScope.sidebarHovered = containsMouse;
                            if (containsMouse) {
                                sidebarHideTimer.stop();
                            } else if (!rightStripSidebarHoverTrigger.containsMouse) {
                                sidebarHideTimer.restart();
                            }
                        }
                    }
                }

                OsdWrapper {
                    id: osdWrapper

                    x: drawersWindow.width - barTotalWidth / 3 - sidebarWrapper.width - sessionWrapper.width - width
                    y: (drawersWindow.height - height) / 2
                    z: 2

                    osdVisible: screenScope.osdVisible

                    onOsdMessageReceived: {
                        screenScope.osdVisible = true;
                        osdAutoHideTimer.restart();
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton

                        onContainsMouseChanged: {
                            rightStripOsdHoverTrigger.osdHovered = containsMouse;
                            if (containsMouse) {
                                osdHideTimer.stop();
                                osdAutoHideTimer.stop();
                            } else if (!rightStripOsdHoverTrigger.containsMouse) {
                                osdHideTimer.restart();
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
                    visible: screenScope.dashboardVisible || screenScope.launcherVisible || screenScope.sessionVisible || screenScope.utilitiesVisible || screenScope.sidebarVisible
                    z: 1

                    onClicked: {
                        screenScope.dashboardVisible = false;
                        screenScope.launcherVisible = false;
                        screenScope.sessionVisible = false;
                        screenScope.utilitiesVisible = false;
                        screenScope.sidebarVisible = false;
                    }

                    Keys.onEscapePressed: {
                        screenScope.dashboardVisible = false;
                        screenScope.launcherVisible = false;
                        screenScope.sessionVisible = false;
                        screenScope.utilitiesVisible = false;
                        screenScope.sidebarVisible = false;
                    }
                    focus: (screenScope.dashboardVisible || screenScope.launcherVisible || screenScope.sessionVisible || screenScope.utilitiesVisible) && !screenScope.sidebarVisible
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
                    id: dashboardShowDelayTimer
                    interval: 200
                    onTriggered: {
                        if (topStripDashboardHoverTrigger.containsMouse)
                            screenScope.dashboardVisible = true;
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

                Timer {
                    id: sessionShowDelayTimer
                    interval: 200
                    onTriggered: {
                        if (rightStripSessionHoverTrigger.containsMouse)
                            screenScope.sessionVisible = true;
                    }
                }

                Timer {
                    id: sessionHideTimer
                    interval: 450
                    onTriggered: {
                        if (!screenScope.sessionHovered && !rightStripSessionHoverTrigger.containsMouse) {
                            screenScope.sessionVisible = false;
                        }
                    }
                }

                Timer {
                    id: utilitiesHideTimer
                    interval: 450
                    onTriggered: {
                        if (!screenScope.utilitiesHovered) {
                            screenScope.utilitiesVisible = false;
                        }
                    }
                }

                Timer {
                    id: sidebarShowDelayTimer
                    interval: 200
                    onTriggered: {
                        if (rightStripSidebarHoverTrigger.containsMouse)
                            screenScope.sidebarVisible = true;
                    }
                }

                Timer {
                    id: sidebarHideTimer
                    interval: 450
                    onTriggered: {
                        if (!screenScope.sidebarHovered && !rightStripSidebarHoverTrigger.containsMouse) {
                            screenScope.sidebarVisible = false;
                        }
                    }
                }

                Timer {
                    id: osdShowDelayTimer
                    interval: 200
                    onTriggered: {
                        if (rightStripOsdHoverTrigger.containsMouse)
                            screenScope.osdVisible = true;
                    }
                }

                Timer {
                    id: osdHideTimer
                    interval: 450
                    onTriggered: {
                        if (!rightStripOsdHoverTrigger.osdHovered && !rightStripOsdHoverTrigger.containsMouse) {
                            screenScope.osdVisible = false;
                        }
                    }
                }

                Timer {
                    id: osdAutoHideTimer
                    interval: 2000
                    onTriggered: screenScope.osdVisible = false
                }
            }

            ExclusionZones {
                screen: screenScope.screen
                barWidth: barTotalWidth
            }
        }
    }
}
