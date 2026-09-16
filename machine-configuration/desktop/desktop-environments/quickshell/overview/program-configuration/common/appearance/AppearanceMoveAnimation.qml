pragma ComponentBehavior: Bound

import QtQuick

QtObject {
    id: root

    property int duration
    property int type: Easing.BezierSpline
    property list<real> bezierCurve
    property Component numberAnimation: Component {
        NumberAnimation {
            duration: root.duration
            easing.type: root.type
            easing.bezierCurve: root.bezierCurve
        }
    }
}
