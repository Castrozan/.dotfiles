pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import QtQuick

Item {
    id: sidebarWrapperRoot

    property bool sidebarVisible: false
    property real contentAvailableHeight: height
    property var hiddenHistoryNotificationIds: ({})

    signal closeRequested()

    visible: width > 0
    width: implicitWidth
    height: implicitHeight
    implicitWidth: 0
    clip: true

    states: State {
        name: "visible"
        when: sidebarWrapperRoot.sidebarVisible

        PropertyChanges {
            sidebarWrapperRoot.implicitWidth: sidebarContentLoader.implicitWidth
        }
    }

    transitions: [
        Transition {
            from: ""
            to: "visible"

            Anim {
                target: sidebarWrapperRoot
                property: "implicitWidth"
                duration: Appearance.anim.durations.expressiveDefaultSpatial
                easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
            }
        },
        Transition {
            from: "visible"
            to: ""

            Anim {
                target: sidebarWrapperRoot
                property: "implicitWidth"
                easing.bezierCurve: Appearance.anim.curves.emphasized
            }
        }
    ]

    Loader {
        id: sidebarContentLoader

        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        active: sidebarWrapperRoot.sidebarVisible || sidebarWrapperRoot.visible

        sourceComponent: SidebarContent {
            availableHeight: sidebarWrapperRoot.contentAvailableHeight
            sidebarActive: sidebarWrapperRoot.sidebarVisible
            hiddenHistoryNotificationIds: sidebarWrapperRoot.hiddenHistoryNotificationIds
            onHiddenHistoryNotificationIdsChanged: sidebarWrapperRoot.hiddenHistoryNotificationIds = hiddenHistoryNotificationIds
        }
    }

    Connections {
        target: sidebarContentLoader.item
        function onCloseRequested(): void {
            sidebarWrapperRoot.closeRequested();
        }
    }
}
