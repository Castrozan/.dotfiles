pragma ComponentBehavior: Bound

import "../components"
import "../services"
import "../widgets"
import ".."
import QtQuick.Layouts

GridLayout {
    id: dashboardTabRoot

    rowSpacing: Appearance.spacing.normal
    columnSpacing: Appearance.spacing.normal

    DashboardCellRect {
        Layout.column: 2
        Layout.columnSpan: 3
        Layout.preferredWidth: userWidget.implicitWidth
        Layout.preferredHeight: userWidget.implicitHeight

        radius: Appearance.rounding.large

        UserWidget {
            id: userWidget
        }
    }

    DashboardCellRect {
        Layout.row: 0
        Layout.columnSpan: 2
        Layout.preferredWidth: DashboardConfig.sizes.weatherWidth
        Layout.fillHeight: true

        radius: Appearance.rounding.large * 1.5

        WeatherWidget {}
    }

    DashboardCellRect {
        Layout.row: 1
        Layout.preferredWidth: dateTimeWidget.implicitWidth
        Layout.fillHeight: true

        radius: Appearance.rounding.normal

        DateTimeWidget {
            id: dateTimeWidget
        }
    }

    DashboardCellRect {
        Layout.row: 1
        Layout.column: 1
        Layout.columnSpan: 3
        Layout.fillWidth: true
        Layout.preferredHeight: calendarWidget.implicitHeight

        radius: Appearance.rounding.large

        CalendarWidget {
            id: calendarWidget
        }
    }

    DashboardCellRect {
        Layout.row: 1
        Layout.column: 4
        Layout.preferredWidth: resourcesWidget.implicitWidth
        Layout.fillHeight: true

        radius: Appearance.rounding.normal

        ResourcesWidget {
            id: resourcesWidget
        }
    }

    DashboardCellRect {
        Layout.row: 0
        Layout.column: 5
        Layout.rowSpan: 2
        Layout.preferredWidth: mediaWidget.implicitWidth
        Layout.fillHeight: true

        radius: Appearance.rounding.large * 2

        MediaWidget {
            id: mediaWidget
        }
    }

    component DashboardCellRect: StyledRect {
        color: Colours.palette.m3surfaceContainer
    }
}
