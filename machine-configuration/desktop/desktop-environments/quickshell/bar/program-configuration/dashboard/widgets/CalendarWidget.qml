pragma ComponentBehavior: Bound

import "../components"
import "calendar"
import ".."
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

MouseArea {
    id: calendarWidgetRoot

    property date currentDate: new Date()

    readonly property int currentMonth: currentDate.getMonth()
    readonly property int currentYear: currentDate.getFullYear()
    readonly property real dayCellHeight: Math.ceil(dayNumberMetrics.height) + Appearance.padding.small * 2

    function weekColumnWidth(availableWidth: real, columnSpacing: real): real {
        return Math.max(0, (availableWidth - 6 * columnSpacing) / 7);
    }

    FontMetrics {
        id: dayNumberMetrics

        font.family: Appearance.font.family.sans
        font.pointSize: Appearance.font.size.normal
        font.weight: 500
    }

    FontMetrics {
        id: weekdayNameMetrics

        font.family: Appearance.font.family.sans
        font.pointSize: Appearance.font.size.smaller
        font.weight: 500
    }

    anchors.left: parent.left
    anchors.right: parent.right
    implicitHeight: calendarInnerLayout.implicitHeight + calendarInnerLayout.anchors.margins * 2

    acceptedButtons: Qt.MiddleButton
    onClicked: calendarWidgetRoot.currentDate = new Date()

    onWheel: wheel => {
        if (wheel.angleDelta.y > 0)
            calendarWidgetRoot.currentDate = new Date(currentYear, currentMonth - 1, 1);
        else if (wheel.angleDelta.y < 0)
            calendarWidgetRoot.currentDate = new Date(currentYear, currentMonth + 1, 1);
    }

    ColumnLayout {
        id: calendarInnerLayout

        anchors.fill: parent
        anchors.margins: Appearance.padding.large
        spacing: Appearance.spacing.small

        CalendarMonthHeader {
            Layout.fillWidth: true
            displayedDate: calendarWidgetRoot.currentDate
            monthNameLocale: monthGrid.locale
            onMonthRequested: requestedDate => calendarWidgetRoot.currentDate = requestedDate
        }

        DayOfWeekRow {
            id: weekdayHeader

            Layout.fillWidth: true
            Layout.preferredHeight: Math.ceil(weekdayNameMetrics.height) + topPadding + bottomPadding
            locale: monthGrid.locale

            delegate: Item {
                id: weekdayDelegate

                required property var model

                implicitWidth: calendarWidgetRoot.weekColumnWidth(weekdayHeader.availableWidth, weekdayHeader.spacing)
                implicitHeight: Math.ceil(weekdayNameMetrics.height)

                StyledText {
                    anchors.centerIn: parent
                    text: weekdayDelegate.model.shortName
                    font.weight: 500
                    color: (weekdayDelegate.model.day === 0 || weekdayDelegate.model.day === 6) ? Colours.palette.m3secondary : Colours.palette.m3onSurfaceVariant
                }
            }
        }

        Item {
            Layout.fillWidth: true
            implicitHeight: calendarWidgetRoot.dayCellHeight * 6 + monthGrid.spacing * 5

            MonthGrid {
                id: monthGrid

                month: calendarWidgetRoot.currentMonth
                year: calendarWidgetRoot.currentYear

                anchors.fill: parent

                spacing: 3
                locale: Qt.locale("en_US")

                delegate: Item {
                    id: dayDelegate

                    required property var model

                    implicitWidth: calendarWidgetRoot.weekColumnWidth(monthGrid.availableWidth, monthGrid.spacing)
                    implicitHeight: calendarWidgetRoot.dayCellHeight

                    StyledText {
                        id: dayLabel

                        anchors.centerIn: parent
                        horizontalAlignment: Text.AlignHCenter
                        text: monthGrid.locale.toString(dayDelegate.model.day)
                        color: {
                            const dayOfWeek = dayDelegate.model.date.getUTCDay();
                            if (dayOfWeek === 0 || dayOfWeek === 6)
                                return Colours.palette.m3secondary;
                            return Colours.palette.m3onSurfaceVariant;
                        }
                        opacity: dayDelegate.model.today || dayDelegate.model.month === monthGrid.month ? 1 : 0.4
                        font.pointSize: Appearance.font.size.normal
                        font.weight: 500
                    }
                }
            }

            CalendarTodayIndicator {
                calendarGrid: monthGrid
            }
        }
    }
}
