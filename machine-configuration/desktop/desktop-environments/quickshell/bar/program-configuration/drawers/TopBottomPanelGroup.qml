import Quickshell
import QtQuick
import "../panels"
import "../dashboard"
import "../launcher"

Scope {
    id: topBottomPanelGroup

    required property Item panelParent
    required property int barTotalWidth
    required property DrawerState drawerState
    required property DrawerHoverController hoverController

    readonly property Item dashboard: dashboardWrapper
    readonly property Item launcher: launcherWrapper

    DashboardWrapper {
        id: dashboardWrapper
        parent: topBottomPanelGroup.panelParent

        x: topBottomPanelGroup.barTotalWidth + (topBottomPanelGroup.panelParent.width - topBottomPanelGroup.barTotalWidth - width) / 2
        y: topBottomPanelGroup.barTotalWidth / 3
        z: 2

        dashboardVisible: topBottomPanelGroup.drawerState.dashboardVisible

        onCloseRequested: topBottomPanelGroup.drawerState.closeDashboard()

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton

            onContainsMouseChanged: containsMouse ? topBottomPanelGroup.hoverController.dashboard.contentEntered() : topBottomPanelGroup.hoverController.dashboard.contentLeft()
        }
    }

    LauncherWrapper {
        id: launcherWrapper
        parent: topBottomPanelGroup.panelParent

        x: topBottomPanelGroup.barTotalWidth + (topBottomPanelGroup.panelParent.width - topBottomPanelGroup.barTotalWidth - width) / 2
        y: topBottomPanelGroup.panelParent.height - topBottomPanelGroup.barTotalWidth / 3 - height
        z: 2

        launcherVisible: topBottomPanelGroup.drawerState.launcherVisible

        onLauncherCloseRequested: topBottomPanelGroup.drawerState.closeLauncher()
        Keys.onEscapePressed: topBottomPanelGroup.drawerState.closeLauncher()

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton

            onContainsMouseChanged: containsMouse ? topBottomPanelGroup.hoverController.launcher.contentEntered() : topBottomPanelGroup.hoverController.launcher.contentLeft()
        }
    }
}
