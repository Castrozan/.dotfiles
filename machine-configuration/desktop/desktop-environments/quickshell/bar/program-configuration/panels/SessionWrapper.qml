pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import QtQuick

Item {
    id: sessionWrapperRoot

    property bool sessionVisible: false

    visible: width > 0
    width: implicitWidth
    height: implicitHeight
    implicitWidth: 0
    implicitHeight: sessionContentLoader.implicitHeight
    clip: true

    states: State {
        name: "visible"
        when: sessionWrapperRoot.sessionVisible

        PropertyChanges {
            sessionWrapperRoot.implicitWidth: sessionContentLoader.implicitWidth
        }
    }

    transitions: [
        Transition {
            from: ""
            to: "visible"

            Anim {
                target: sessionWrapperRoot
                property: "implicitWidth"
                duration: Appearance.anim.durations.expressiveDefaultSpatial
                easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
            }
        },
        Transition {
            from: "visible"
            to: ""

            Anim {
                target: sessionWrapperRoot
                property: "implicitWidth"
                easing.bezierCurve: Appearance.anim.curves.emphasized
            }
        }
    ]

    Loader {
        id: sessionContentLoader

        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter

        active: sessionWrapperRoot.sessionVisible || sessionWrapperRoot.visible

        sourceComponent: SessionContent {}
    }
}
