pragma ComponentBehavior: Bound

import "../../components"
import "../.."
import QtQuick
import QtQuick.Controls

StyledRect {
    id: todayHighlightIndicator

    required property MonthGrid calendarGrid

    readonly property Item todayItem: calendarGrid.contentItem.children.find(child => child.model?.today) ?? null
    property Item todayTarget

    onTodayItemChanged: {
        if (todayItem)
            todayTarget = todayItem;
    }

    x: todayTarget ? todayTarget.x + (todayTarget.width - implicitWidth) / 2 : 0
    y: todayTarget?.y ?? 0

    implicitWidth: todayTarget?.implicitWidth ?? 0
    implicitHeight: todayTarget?.implicitHeight ?? 0

    clip: true
    radius: Appearance.rounding.full
    color: Colours.palette.m3primary

    opacity: todayItem ? 1 : 0
    scale: todayItem ? 1 : 0.7

    StyledText {
        anchors.centerIn: parent
        horizontalAlignment: Text.AlignHCenter
        text: {
            const now = new Date();
            return calendarGrid.locale.toString(now.getDate());
        }
        color: Colours.palette.m3onPrimary
        font.pointSize: Appearance.font.size.normal
        font.weight: 500
    }

    Behavior on opacity {
        Anim {}
    }

    Behavior on scale {
        Anim {}
    }

    Behavior on x {
        Anim {
            duration: Appearance.anim.durations.expressiveDefaultSpatial
            easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
        }
    }

    Behavior on y {
        Anim {
            duration: Appearance.anim.durations.expressiveDefaultSpatial
            easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
        }
    }
}
