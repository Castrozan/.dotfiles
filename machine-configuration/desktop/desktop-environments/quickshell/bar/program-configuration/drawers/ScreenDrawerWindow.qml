import Quickshell
import Quickshell.Wayland
import QtQuick
import "../bar"
import "../frame"
import "../popouts"

PanelWindow {
    id: drawersWindow

    required property int barTotalWidth
    required property int shapeJunctionRadius
    required property bool activeWorkspaceHasFullscreenWindow
    required property bool activeWorkspaceIsEmpty
    required property DrawerState drawerState
    required property DrawerHoverController hoverController

    readonly property Item barItem: barWrapper.barItem
    readonly property bool pointerOverBar: interactions.isOverBar
    readonly property real visibleBarWidth: Math.max(0, barWrapper.x + barWrapper.width)

    property real animatedExtensionWidth: drawerState.hasActivePopout ? popoutWrapper.popoutWidth : 0
    Behavior on animatedExtensionWidth {
        NumberAnimation {
            duration: 350
            easing.type: Easing.OutCubic
        }
    }

    function handleOsdMessage(message: string): void {
        rightPanels.osd.handleOsdMessage(message);
    }

    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }

    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: drawersWindow.activeWorkspaceHasFullscreenWindow ? WlrLayer.Background : WlrLayer.Top
    WlrLayershell.namespace: "quickshell-bar"
    WlrLayershell.keyboardFocus: drawersWindow.drawerState.hasAnyPanelVisible ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

    color: "transparent"
    surfaceFormat.opaque: false

    mask: DrawerInputMask {
        edgeGeometry: edgeGeometry
        leftBarWidth: drawersWindow.visibleBarWidth
        shapeJunctionRadius: drawersWindow.shapeJunctionRadius
        popoutItem: popoutWrapper
        dashboardItem: topBottomPanels.dashboard
        launcherItem: topBottomPanels.launcher
        sessionItem: rightPanels.session
        utilitiesItem: rightPanels.utilities
        osdItem: rightPanels.osd
        sidebarItem: rightPanels.sidebar
    }

    RightPanelGeometry {
        id: aggregatedRightPanelGeometry
        sessionItem: rightPanels.session
        sidebarItem: rightPanels.sidebar
        utilitiesItem: rightPanels.utilities
        osdItem: rightPanels.osd
    }

    BarBackgroundShape {
        id: barBackgroundShape
        anchors.fill: parent
        z: 0
        visible: drawersWindow.activeWorkspaceIsEmpty || drawersWindow.visibleBarWidth > 0 || drawersWindow.animatedExtensionWidth > 0 || topBottomPanels.dashboard.visible || topBottomPanels.launcher.visible || aggregatedRightPanelGeometry.aggregatedWidth > 0
        desktopBorderVisible: drawersWindow.activeWorkspaceIsEmpty
        geometry: BarFrameGeometry {
            leftBarWidth: drawersWindow.visibleBarWidth
            barHeight: drawersWindow.height
            screenWidth: drawersWindow.width
            junctionRadius: drawersWindow.shapeJunctionRadius
            extensionY: popoutWrapper.y
            extensionHeight: popoutWrapper.hasContent ? popoutWrapper.height : 0
            extensionWidth: drawersWindow.animatedExtensionWidth
            dashboardX: topBottomPanels.dashboard.x
            dashboardWidth: topBottomPanels.dashboard.visible ? topBottomPanels.dashboard.width : 0
            dashboardHeight: topBottomPanels.dashboard.visible ? topBottomPanels.dashboard.height : 0
            launcherX: topBottomPanels.launcher.x
            launcherWidth: topBottomPanels.launcher.visible ? topBottomPanels.launcher.width : 0
            launcherHeight: topBottomPanels.launcher.visible ? topBottomPanels.launcher.height : 0
            rightPanelY: aggregatedRightPanelGeometry.aggregatedY
            rightPanelWidth: aggregatedRightPanelGeometry.aggregatedWidth
            rightPanelHeight: aggregatedRightPanelGeometry.aggregatedHeight
        }
    }

    Interactions {
        id: interactions
        anchors.fill: parent
        barWidth: barWrapper.visible ? drawersWindow.visibleBarWidth : 0
        barComponent: barWrapper.barItem

        onPopoutAreaLeft: drawersWindow.drawerState.hidePopout()
    }

    BarWrapper {
        id: barWrapper
        width: drawersWindow.barTotalWidth
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        screenScope: drawersWindow.drawerState
        barVisible: drawersWindow.drawerState.barVisible

        onHoverChanged: hovered => hovered ? drawersWindow.hoverController.bar.contentEntered() : drawersWindow.hoverController.bar.contentLeft()
    }

    TopBottomPanelGroup {
        id: topBottomPanels
        panelParent: drawersWindow.contentItem
        drawerState: drawersWindow.drawerState
        hoverController: drawersWindow.hoverController
    }

    ScreenEdgeGeometry {
        id: edgeGeometry
        windowWidth: drawersWindow.width
        windowHeight: drawersWindow.height
    }

    ScreenEdgeHoverAreas {
        geometry: edgeGeometry
        hoverController: drawersWindow.hoverController
    }

    RightPanelGroup {
        id: rightPanels
        panelParent: drawersWindow.contentItem
        drawerState: drawersWindow.drawerState
        hoverController: drawersWindow.hoverController
    }

    PopoutWrapper {
        id: popoutWrapper
        x: drawersWindow.visibleBarWidth
        currentName: drawersWindow.drawerState.popoutCurrentName
        currentCenterY: drawersWindow.drawerState.popoutCenterY
        screenHeight: drawersWindow.height

        onContainsMouseChanged: containsMouse ? drawersWindow.hoverController.popoutContentEntered() : drawersWindow.hoverController.popoutContentLeft()
    }

    MouseArea {
        id: drawersDismissArea

        anchors.fill: parent
        visible: drawersWindow.drawerState.hasAnyPanelVisible
        z: 1

        onClicked: drawersWindow.drawerState.closeAllPanels()

        Keys.onEscapePressed: drawersWindow.drawerState.closeAllPanels()
        focus: (drawersWindow.drawerState.launcherVisible || drawersWindow.drawerState.sessionVisible || drawersWindow.drawerState.utilitiesVisible) && !drawersWindow.drawerState.sidebarVisible && !drawersWindow.drawerState.dashboardVisible
    }
}
