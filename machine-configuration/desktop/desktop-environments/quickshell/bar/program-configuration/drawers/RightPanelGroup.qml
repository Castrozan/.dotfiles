import Quickshell
import QtQuick
import "../panels"
import "../dashboard"
import "../launcher"

Scope {
    id: rightPanelGroup

    required property Item panelParent
    required property DrawerState drawerState
    required property DrawerHoverController hoverController

    readonly property Item session: sessionWrapper
    readonly property Item utilities: utilitiesWrapper
    readonly property Item sidebar: sidebarWrapper
    readonly property Item osd: osdWrapper

    SessionWrapper {
        id: sessionWrapper
        parent: rightPanelGroup.panelParent

        x: rightPanelGroup.panelParent.width - sidebarWrapper.width - width
        y: (rightPanelGroup.panelParent.height - height) / 2
        z: 2

        sessionVisible: rightPanelGroup.drawerState.sessionVisible

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton

            onContainsMouseChanged: containsMouse ? rightPanelGroup.hoverController.session.contentEntered() : rightPanelGroup.hoverController.session.contentLeft()
        }
    }

    UtilitiesWrapper {
        id: utilitiesWrapper
        parent: rightPanelGroup.panelParent

        x: rightPanelGroup.panelParent.width - width
        y: rightPanelGroup.panelParent.height - height
        z: 3

        utilitiesVisible: rightPanelGroup.drawerState.utilitiesVisible

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton

            onContainsMouseChanged: containsMouse ? rightPanelGroup.hoverController.utilities.contentEntered() : rightPanelGroup.hoverController.utilities.contentLeft()
        }
    }

    SidebarWrapper {
        id: sidebarWrapper
        parent: rightPanelGroup.panelParent

        readonly property real sidebarTopEdge: 0
        readonly property real sidebarBottomEdge: rightPanelGroup.panelParent.height

        x: rightPanelGroup.panelParent.width - width
        y: sidebarTopEdge
        z: 2
        height: sidebarBottomEdge - sidebarTopEdge

        sidebarVisible: rightPanelGroup.drawerState.sidebarVisible
        contentAvailableHeight: sidebarBottomEdge - sidebarTopEdge - utilitiesWrapper.height

        onCloseRequested: rightPanelGroup.drawerState.closeSidebar()

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton

            onContainsMouseChanged: containsMouse ? rightPanelGroup.hoverController.sidebar.contentEntered() : rightPanelGroup.hoverController.sidebar.contentLeft()
        }
    }

    OsdWrapper {
        id: osdWrapper
        parent: rightPanelGroup.panelParent

        x: rightPanelGroup.panelParent.width - sidebarWrapper.width - sessionWrapper.width - width
        y: (rightPanelGroup.panelParent.height - height) / 2
        z: 2

        osdVisible: rightPanelGroup.drawerState.osdVisible

        onOsdMessageReceived: rightPanelGroup.hoverController.showOsdTemporarily()

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton

            onContainsMouseChanged: containsMouse ? rightPanelGroup.hoverController.osd.contentEntered() : rightPanelGroup.hoverController.osd.contentLeft()
        }
    }
}
