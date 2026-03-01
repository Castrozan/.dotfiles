pragma ComponentBehavior: Bound

import "../dashboard/components"
import "../dashboard"
import QtQuick

Item {
    id: utilitiesWrapperRoot

    property bool utilitiesVisible: false

    visible: height > 0
    width: implicitWidth
    height: implicitHeight
    implicitWidth: utilitiesContentLoader.implicitWidth
    implicitHeight: 0
    clip: true

    states: State {
        name: "visible"
        when: utilitiesWrapperRoot.utilitiesVisible

        PropertyChanges {
            utilitiesWrapperRoot.implicitHeight: utilitiesContentLoader.implicitHeight
        }
    }

    transitions: [
        Transition {
            from: ""
            to: "visible"

            Anim {
                target: utilitiesWrapperRoot
                property: "implicitHeight"
                duration: Appearance.anim.durations.expressiveDefaultSpatial
                easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
            }
        },
        Transition {
            from: "visible"
            to: ""

            Anim {
                target: utilitiesWrapperRoot
                property: "implicitHeight"
                easing.bezierCurve: Appearance.anim.curves.emphasized
            }
        }
    ]

    Loader {
        id: utilitiesContentLoader

        anchors.right: parent.right
        anchors.bottom: parent.bottom

        active: utilitiesWrapperRoot.utilitiesVisible || utilitiesWrapperRoot.visible

        sourceComponent: UtilitiesContent {}
    }
}
