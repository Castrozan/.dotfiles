pragma ComponentBehavior: Bound

import "components"
import "."
import QtQuick

Item {
    id: dashboardWrapperRoot

    property bool dashboardVisible: false
    readonly property real contentHeight: dashboardContentLoader.item?.nonAnimatedHeight ?? 0

    visible: height > 0
    width: implicitWidth
    height: implicitHeight
    implicitHeight: 0
    implicitWidth: dashboardContentLoader.implicitWidth
    clip: true

    states: State {
        name: "visible"
        when: dashboardWrapperRoot.dashboardVisible

        PropertyChanges {
            dashboardWrapperRoot.implicitHeight: dashboardContentLoader.implicitHeight
        }
    }

    transitions: [
        Transition {
            from: ""
            to: "visible"

            Anim {
                target: dashboardWrapperRoot
                property: "implicitHeight"
                duration: Appearance.anim.durations.expressiveDefaultSpatial
                easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
            }
        },
        Transition {
            from: "visible"
            to: ""

            Anim {
                target: dashboardWrapperRoot
                property: "implicitHeight"
                easing.bezierCurve: Appearance.anim.curves.emphasized
            }
        }
    ]

    Loader {
        id: dashboardContentLoader

        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom

        active: dashboardWrapperRoot.dashboardVisible || dashboardWrapperRoot.visible

        sourceComponent: DashboardContent {}
    }
}
