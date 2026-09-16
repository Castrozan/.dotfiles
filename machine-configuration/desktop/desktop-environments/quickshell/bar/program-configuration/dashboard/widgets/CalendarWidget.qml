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

        RowLayout {
            Layout.fillWidth: true
            spacing: Appearance.spacing.small

            Item {
                implicitWidth: implicitHeight
                implicitHeight: previousMonthIcon.implicitHeight + Appearance.padding.small * 2

                StateLayer {
                    radius: Appearance.rounding.full

                    function onClicked(): void {
                        calendarWidgetRoot.currentDate = new Date(calendarWidgetRoot.currentYear, calendarWidgetRoot.currentMonth - 1, 1);
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
                        return calendarWidgetRoot.currentMonth === now.getMonth() && calendarWidgetRoot.currentYear === now.getFullYear();
                    }

                    function onClicked(): void {
                        calendarWidgetRoot.currentDate = new Date();
                    }
                }

                StyledText {
                    id: monthYearLabel

                    anchors.centerIn: parent
                    text: monthGrid.title
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
                        calendarWidgetRoot.currentDate = new Date(calendarWidgetRoot.currentYear, calendarWidgetRoot.currentMonth + 1, 1);
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

        DayOfWeekRow {
            Layout.fillWidth: true
            locale: monthGrid.locale

            delegate: StyledText {
                required property var model

                horizontalAlignment: Text.AlignHCenter
                text: model.shortName
                font.weight: 500
                color: (model.day === 0 || model.day === 6) ? Colours.palette.m3secondary : Colours.palette.m3onSurfaceVariant
            }
        }

        Item {
            Layout.fillWidth: true
            implicitHeight: monthGrid.implicitHeight

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

                    implicitWidth: implicitHeight
                    implicitHeight: dayLabel.implicitHeight + Appearance.padding.small * 2

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
