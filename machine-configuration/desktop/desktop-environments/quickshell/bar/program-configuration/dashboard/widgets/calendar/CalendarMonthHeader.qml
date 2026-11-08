pragma ComponentBehavior: Bound

import "../../components"
import "../.."
import QtQuick
import QtQuick.Layouts

RowLayout {
    id: calendarMonthHeaderRoot

    required property date displayedDate
    required property var monthNameLocale

    readonly property int displayedMonth: displayedDate.getMonth()
    readonly property int displayedYear: displayedDate.getFullYear()

    signal monthRequested(date requestedDate)

    spacing: Appearance.spacing.small

    Item {
        implicitWidth: implicitHeight
        implicitHeight: previousMonthIcon.implicitHeight + Appearance.padding.small * 2

        StateLayer {
            radius: Appearance.rounding.full

            function onClicked(): void {
                calendarMonthHeaderRoot.monthRequested(new Date(calendarMonthHeaderRoot.displayedYear, calendarMonthHeaderRoot.displayedMonth - 1, 1));
            }
        }

        MaterialIcon {
            id: previousMonthIcon

            anchors.centerIn: parent
            text: "chevron_left"
            color: Colours.palette.m3tertiary
            font.pointSize: Appearance.font.size.normal
            font.weight: 700
        }
    }

    Item {
        Layout.fillWidth: true

        implicitWidth: monthYearLabel.implicitWidth + Appearance.padding.small * 2
        implicitHeight: monthYearLabel.implicitHeight + Appearance.padding.small * 2

        StateLayer {
            anchors.fill: monthYearLabel
            anchors.margins: -Appearance.padding.small
            anchors.leftMargin: -Appearance.padding.normal
            anchors.rightMargin: -Appearance.padding.normal

            radius: Appearance.rounding.full
            disabled: {
                const now = new Date();
                return calendarMonthHeaderRoot.displayedMonth === now.getMonth() && calendarMonthHeaderRoot.displayedYear === now.getFullYear();
            }

            function onClicked(): void {
                calendarMonthHeaderRoot.monthRequested(new Date());
            }
        }

        StyledText {
            id: monthYearLabel

            anchors.centerIn: parent
            text: calendarMonthHeaderRoot.monthNameLocale.standaloneMonthName(calendarMonthHeaderRoot.displayedMonth) + " " + calendarMonthHeaderRoot.displayedYear
            color: Colours.palette.m3primary
            font.pointSize: Appearance.font.size.normal
            font.weight: 500
            font.capitalization: Font.Capitalize
        }
    }

    Item {
        implicitWidth: implicitHeight
        implicitHeight: nextMonthIcon.implicitHeight + Appearance.padding.small * 2

        StateLayer {
            radius: Appearance.rounding.full

            function onClicked(): void {
                calendarMonthHeaderRoot.monthRequested(new Date(calendarMonthHeaderRoot.displayedYear, calendarMonthHeaderRoot.displayedMonth + 1, 1));
            }
        }

        MaterialIcon {
            id: nextMonthIcon

            anchors.centerIn: parent
            text: "chevron_right"
            color: Colours.palette.m3tertiary
            font.pointSize: Appearance.font.size.normal
            font.weight: 700
        }
    }
}
