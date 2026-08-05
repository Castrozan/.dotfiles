import Quickshell.Widgets
import QtQuick

ClippingRectangle {
    id: styledClippingRectRoot

    color: "transparent"

    Behavior on color {
        CAnim {}
    }
}
