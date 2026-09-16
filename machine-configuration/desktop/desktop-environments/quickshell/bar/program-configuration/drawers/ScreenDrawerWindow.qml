import Quickshell
import Quickshell.Wayland
import QtQuick
import QtQuick.Shapes
import "../bar"
import "../frame"
import "../popouts"

PanelWindow {
    id: drawersWindow

    required property int barTotalWidth
    required property int shapeJunctionRadius
    required property bool activeWorkspaceHasFullscreenWindow
    required property DrawerState drawerState
    required property DrawerHoverController hoverController

    readonly property Item barItem: barWrapper.barItem
    readonly property bool pointerOverBar: interactions.isOverBar
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
        barTotalWidth: drawersWindow.barTotalWidth
        windowWidth: drawersWindow.width
        windowHeight: drawersWindow.height
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

    Shape {
        id: barBackgroundShape
        anchors.fill: parent
        z: 0
        preferredRendererType: Shape.CurveRenderer

        BarBackgroundShape {
            barWidth: barTotalWidth
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

    Shape {
        anchors.fill: parent
        z: 1
        preferredRendererType: Shape.CurveRenderer

        BarInternalBorderShape {
            barWidth: barTotalWidth
            barHeight: drawersWindow.height
            screenWidth: drawersWindow.width
            junctionRadius: drawersWindow.shapeJunctionRadius
            extensionY: popoutWrapper.y
            extensionHeight: popoutWrapper.hasContent ? popoutWrapper.height : 0
            extensionWidth: drawersWindow.animatedExtensionWidth
            dashboardX: topBottomPanels.dashboard.x
            dashboardWidth: topBottomPanels.dashboard.visible ? topBottomPanels.dashboard.width : 0
            dashboardHeight: topBottomPanels.dashboard.visible ? topBottomPanels.dashboard.height : 0
            rightPanelY: aggregatedRightPanelGeometry.aggregatedY
            rightPanelWidth: aggregatedRightPanelGeometry.aggregatedWidth
            rightPanelHeight: aggregatedRightPanelGeometry.aggregatedHeight
            launcherX: topBottomPanels.launcher.x
            launcherWidth: topBottomPanels.launcher.visible ? topBottomPanels.launcher.width : 0
            launcherHeight: topBottomPanels.launcher.visible ? topBottomPanels.launcher.height : 0
        }
    }

    Interactions {
        id: interactions
        anchors.fill: parent
        barWidth: barTotalWidth
        barComponent: barWrapper.barItem

        onPopoutAreaLeft: drawersWindow.drawerState.hidePopout()
    }

    BarWrapper {
        id: barWrapper
        width: barTotalWidth
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: parent.left

        screenScope: drawersWindow.drawerState
    }

    TopBottomPanelGroup {
        id: topBottomPanels
        panelParent: drawersWindow.contentItem
        barTotalWidth: drawersWindow.barTotalWidth
        drawerState: drawersWindow.drawerState
        hoverController: drawersWindow.hoverController
    }

    ScreenEdgeHoverAreas {
        barTotalWidth: drawersWindow.barTotalWidth
        hoverController: drawersWindow.hoverController
    }

    RightPanelGroup {
        id: rightPanels
        panelParent: drawersWindow.contentItem
        barTotalWidth: drawersWindow.barTotalWidth
        drawerState: drawersWindow.drawerState
        hoverController: drawersWindow.hoverController
    }

    PopoutWrapper {
        id: popoutWrapper
        x: barTotalWidth
        currentName: drawersWindow.drawerState.popoutCurrentName
        currentCenterY: drawersWindow.drawerState.popoutCenterY
        screenHeight: drawersWindow.height
        barWidth: barTotalWidth

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
