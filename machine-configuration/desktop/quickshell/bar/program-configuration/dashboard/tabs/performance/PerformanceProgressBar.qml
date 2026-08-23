pragma ComponentBehavior: Bound

import "../../components"
import "../.."
import QtQuick

StyledRect {
    id: performanceProgressBarRoot

    property real value: 0
    property color foregroundColor: Colours.palette.m3primary
    property color backgroundColor: Colours.layer(Colours.palette.m3surfaceContainerHigh, 2)
    property real animatedValue: 0

    color: backgroundColor
    radius: Appearance.rounding.full
    Component.onCompleted: animatedValue = value
    onValueChanged: animatedValue = value

    StyledRect {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        width: parent.width * performanceProgressBarRoot.animatedValue
        color: performanceProgressBarRoot.foregroundColor
        radius: Appearance.rounding.full
    }

    Behavior on animatedValue {
        Anim {
            duration: Appearance.anim.durations.large
        }
    }
}
