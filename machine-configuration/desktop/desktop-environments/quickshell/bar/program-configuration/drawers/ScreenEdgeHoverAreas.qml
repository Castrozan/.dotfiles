import QtQuick

Item {
    id: edgeHoverAreas

    required property int barTotalWidth
    required property DrawerHoverController hoverController

    anchors.fill: parent
    z: 3

    MouseArea {
        id: topStripDashboardHoverTrigger

        readonly property real topStripHeight: 2
        readonly property real triggerWidth: edgeHoverAreas.width - edgeHoverAreas.barTotalWidth * 2

        x: edgeHoverAreas.barTotalWidth + (edgeHoverAreas.width - edgeHoverAreas.barTotalWidth - triggerWidth) / 2
        y: 0
        z: 3
        width: triggerWidth
        height: topStripHeight

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.dashboard.triggerEntered() : edgeHoverAreas.hoverController.dashboard.triggerLeft()
    }

    MouseArea {
        id: bottomStripLauncherHoverTrigger

        readonly property real bottomStripHeight: 2
        readonly property real triggerWidth: edgeHoverAreas.width - edgeHoverAreas.barTotalWidth * 2

        x: edgeHoverAreas.barTotalWidth + (edgeHoverAreas.width - edgeHoverAreas.barTotalWidth - triggerWidth) / 2
        y: edgeHoverAreas.height - bottomStripHeight
        z: 3
        width: triggerWidth
        height: bottomStripHeight

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.launcher.triggerEntered() : edgeHoverAreas.hoverController.launcher.triggerLeft()
    }

    MouseArea {
        id: rightStripSidebarHoverTrigger

        readonly property real rightStripWidth: edgeHoverAreas.barTotalWidth / 3
        readonly property real rightStripInnerTop: edgeHoverAreas.barTotalWidth / 3
        readonly property real rightStripInnerHeight: edgeHoverAreas.height - edgeHoverAreas.barTotalWidth * 2 / 3
        readonly property real zoneHeight: rightStripInnerHeight / 3

        x: edgeHoverAreas.width - rightStripWidth
        y: rightStripInnerTop
        z: 3
        width: rightStripWidth
        height: zoneHeight

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.sidebar.triggerEntered() : edgeHoverAreas.hoverController.sidebar.triggerLeft()
    }

    MouseArea {
        id: rightStripOsdHoverTrigger

        x: edgeHoverAreas.width - rightStripSidebarHoverTrigger.rightStripWidth
        y: rightStripSidebarHoverTrigger.rightStripInnerTop + rightStripSidebarHoverTrigger.zoneHeight
        z: 3
        width: rightStripSidebarHoverTrigger.rightStripWidth
        height: rightStripSidebarHoverTrigger.zoneHeight

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.osd.triggerEntered() : edgeHoverAreas.hoverController.osd.triggerLeft()
    }

    MouseArea {
        id: rightStripSessionHoverTrigger

        x: edgeHoverAreas.width - rightStripSidebarHoverTrigger.rightStripWidth
        y: rightStripSidebarHoverTrigger.rightStripInnerTop + rightStripSidebarHoverTrigger.zoneHeight * 2
        z: 3
        width: rightStripSidebarHoverTrigger.rightStripWidth
        height: rightStripSidebarHoverTrigger.zoneHeight

        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onContainsMouseChanged: containsMouse ? edgeHoverAreas.hoverController.session.triggerEntered() : edgeHoverAreas.hoverController.session.triggerLeft()
    }
}
