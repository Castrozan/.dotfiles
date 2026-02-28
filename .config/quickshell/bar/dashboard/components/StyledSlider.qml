pragma ComponentBehavior: Bound

import ".."
import QtQuick
import QtQuick.Templates

Slider {
    id: styledSliderRoot

    background: Item {
        StyledRect {
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.topMargin: styledSliderRoot.implicitHeight / 3
            anchors.bottomMargin: styledSliderRoot.implicitHeight / 3

            implicitWidth: styledSliderRoot.handle.x - styledSliderRoot.implicitHeight / 6

            color: Colours.palette.m3primary
            radius: Appearance.rounding.full
            topRightRadius: styledSliderRoot.implicitHeight / 15
            bottomRightRadius: styledSliderRoot.implicitHeight / 15
        }

        StyledRect {
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            anchors.topMargin: styledSliderRoot.implicitHeight / 3
            anchors.bottomMargin: styledSliderRoot.implicitHeight / 3

            implicitWidth: parent.width - styledSliderRoot.handle.x - styledSliderRoot.handle.implicitWidth - styledSliderRoot.implicitHeight / 6

            color: Colours.palette.m3surfaceContainerHighest
            radius: Appearance.rounding.full
            topLeftRadius: styledSliderRoot.implicitHeight / 15
            bottomLeftRadius: styledSliderRoot.implicitHeight / 15
        }
    }

    handle: StyledRect {
        x: styledSliderRoot.visualPosition * styledSliderRoot.availableWidth - implicitWidth / 2

        implicitWidth: styledSliderRoot.implicitHeight / 4.5
        implicitHeight: styledSliderRoot.implicitHeight

        color: Colours.palette.m3primary
        radius: Appearance.rounding.full

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            cursorShape: Qt.PointingHandCursor
        }
    }
}
