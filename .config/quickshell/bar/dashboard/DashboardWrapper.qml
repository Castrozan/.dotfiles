pragma ComponentBehavior: Bound

import "components"
import "."
import QtQuick

Item {
    id: dashboardWrapperRoot

    property bool dashboardVisible: false
    readonly property real contentHeight: dashboardContentLoader.item?.nonAnimatedHeight ?? 0
    readonly property int tabCount: dashboardContentLoader.item?.tabCount ?? 0

    signal closeRequested()

    visible: height > 0
    width: implicitWidth
    height: implicitHeight
    implicitHeight: 0
    implicitWidth: dashboardContentLoader.implicitWidth
    clip: true
    focus: dashboardVisible

    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape) {
            dashboardWrapperRoot.closeRequested();
            event.accepted = true;
        } else if (event.key === Qt.Key_Tab) {
            if (!dashboardContentLoader.item)
                return;
            if (event.modifiers & Qt.ShiftModifier)
                dashboardContentLoader.item.currentTabIndex = (dashboardContentLoader.item.currentTabIndex - 1 + dashboardWrapperRoot.tabCount) % dashboardWrapperRoot.tabCount;
            else
                dashboardContentLoader.item.currentTabIndex = (dashboardContentLoader.item.currentTabIndex + 1) % dashboardWrapperRoot.tabCount;
            event.accepted = true;
        } else if (event.key === Qt.Key_Down || event.key === Qt.Key_Up || event.key === Qt.Key_Left || event.key === Qt.Key_Right || event.key === Qt.Key_Return || event.key === Qt.Key_Space) {
            if (dashboardContentLoader.item?.activateCurrentTabKeyboardNavigation)
                dashboardContentLoader.item.activateCurrentTabKeyboardNavigation();
            event.accepted = true;
        }
    }

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

        active: true

        sourceComponent: DashboardContent {
            dashboardIsActive: dashboardWrapperRoot.dashboardVisible
        }
    }
}
