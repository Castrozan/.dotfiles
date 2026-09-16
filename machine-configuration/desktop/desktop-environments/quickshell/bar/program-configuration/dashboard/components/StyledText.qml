pragma ComponentBehavior: Bound

import ".."
import QtQuick

Text {
    id: styledTextRoot

    property bool animate: false
    property string animateProp: "scale"
    property real animateFrom: 0
    property real animateTo: 1
    property int animateDuration: Appearance.anim.durations.normal

    renderType: Text.NativeRendering
    textFormat: Text.PlainText
    color: Colours.palette.m3onSurface
    font.family: Appearance.font.family.sans
    font.pointSize: Appearance.font.size.smaller

    Behavior on color {
        CAnim {}
    }

    Behavior on text {
        enabled: styledTextRoot.animate

        SequentialAnimation {
            NumberAnimation {
                target: styledTextRoot
                property: styledTextRoot.animateProp
                to: styledTextRoot.animateFrom
                duration: styledTextRoot.animateDuration / 2
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Appearance.anim.curves.standardAccel
            }
            PropertyAction {}
            NumberAnimation {
                target: styledTextRoot
                property: styledTextRoot.animateProp
                to: styledTextRoot.animateTo
                duration: styledTextRoot.animateDuration / 2
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Appearance.anim.curves.standardDecel
            }
        }
    }
}
