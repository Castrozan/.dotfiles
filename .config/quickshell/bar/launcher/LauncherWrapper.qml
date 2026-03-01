pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import QtQuick

Item {
    id: launcherWrapperRoot

    property bool launcherVisible: false
    readonly property real contentWidth: launcherContentLoader.item?.implicitWidth ?? 0

    visible: height > 0
    width: implicitWidth
    height: implicitHeight
    implicitHeight: 0
    implicitWidth: launcherContentLoader.implicitWidth
    clip: true

    states: State {
        name: "visible"
        when: launcherWrapperRoot.launcherVisible

        PropertyChanges {
            launcherWrapperRoot.implicitHeight: launcherContentLoader.implicitHeight
        }
    }

    transitions: [
        Transition {
            from: ""
            to: "visible"

            Anim {
                target: launcherWrapperRoot
                property: "implicitHeight"
                duration: Appearance.anim.durations.expressiveDefaultSpatial
                easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
            }
        },
        Transition {
            from: "visible"
            to: ""

            Anim {
                target: launcherWrapperRoot
                property: "implicitHeight"
                easing.bezierCurve: Appearance.anim.curves.emphasized
            }
        }
    ]

    Loader {
        id: launcherContentLoader

        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom

        active: launcherWrapperRoot.launcherVisible || launcherWrapperRoot.visible

        sourceComponent: LauncherContent {
            launcherVisible: launcherWrapperRoot.launcherVisible
        }
    }
}
