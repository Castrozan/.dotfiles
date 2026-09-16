pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

IconButton {
    Layout.preferredWidth: implicitWidth + (stateLayer.pressed ? Appearance.padding.large : internalChecked ? Appearance.padding.smaller : 0)
    radius: stateLayer.pressed ? Appearance.rounding.small / 2 : internalChecked ? Appearance.rounding.small : implicitHeight / 2

    Behavior on Layout.preferredWidth {
        Anim {
            duration: Appearance.anim.durations.expressiveFastSpatial
            easing.bezierCurve: Appearance.anim.curves.expressiveFastSpatial
        }
    }
}
