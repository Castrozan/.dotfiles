import QtQuick

Item {
    id: edgeHoverAreas

    required property ScreenEdgeGeometry geometry
    required property DrawerHoverController hoverController

    anchors.fill: parent
    z: 3

    MouseArea {
        readonly property rect trigger: edgeHoverAreas.geometry.leftTrigger

        x: trigger.x
        y: trigger.y
        width: trigger.width
        height: trigger.height

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.bar.triggerEntered() : edgeHoverAreas.hoverController.bar.triggerLeft()
    }

    MouseArea {
        readonly property rect trigger: edgeHoverAreas.geometry.topTrigger

        x: trigger.x
        y: trigger.y
        width: trigger.width
        height: trigger.height

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.dashboard.triggerEntered() : edgeHoverAreas.hoverController.dashboard.triggerLeft()
    }

    MouseArea {
        readonly property rect trigger: edgeHoverAreas.geometry.bottomTrigger

        x: trigger.x
        y: trigger.y
        width: trigger.width
        height: trigger.height

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.launcher.triggerEntered() : edgeHoverAreas.hoverController.launcher.triggerLeft()
    }

    MouseArea {
        readonly property rect trigger: edgeHoverAreas.geometry.sidebarTrigger

        x: trigger.x
        y: trigger.y
        width: trigger.width
        height: trigger.height

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.sidebar.triggerEntered() : edgeHoverAreas.hoverController.sidebar.triggerLeft()
    }

    MouseArea {
        readonly property rect trigger: edgeHoverAreas.geometry.sessionTrigger

        x: trigger.x
        y: trigger.y
        width: trigger.width
        height: trigger.height

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.session.triggerEntered() : edgeHoverAreas.hoverController.session.triggerLeft()
    }
}
