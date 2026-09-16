pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

StyledRect {
    id: forecastDayItem

    required property int index
    required property var modelData

    Layout.fillWidth: true
    implicitHeight: forecastDayColumn.implicitHeight + Appearance.padding.normal * 2

    radius: Appearance.rounding.normal
    color: Colours.tPalette.m3surfaceContainer

    ColumnLayout {
        id: forecastDayColumn

        anchors.centerIn: parent
        spacing: Appearance.spacing.small

        StyledText {
            Layout.alignment: Qt.AlignHCenter
            text: forecastDayItem.index === 0 ? "Today" : new Date(forecastDayItem.modelData.date).toLocaleDateString(Qt.locale("en_US"), "ddd")
            font.pointSize: Appearance.font.size.normal
            font.weight: 600
            color: Colours.palette.m3primary
        }

        StyledText {
            Layout.topMargin: -Appearance.spacing.small / 2
            Layout.alignment: Qt.AlignHCenter
            text: new Date(forecastDayItem.modelData.date).toLocaleDateString(Qt.locale("en_US"), "MMM d")
            font.pointSize: Appearance.font.size.small
            opacity: 0.7
            color: Colours.palette.m3onSurfaceVariant
        }

        MaterialIcon {
            Layout.alignment: Qt.AlignHCenter
            text: forecastDayItem.modelData.icon
            font.pointSize: Appearance.font.size.extraLarge
            color: Colours.palette.m3secondary
        }

        StyledText {
            Layout.alignment: Qt.AlignHCenter
            text: DashboardConfig.useFahrenheit ? forecastDayItem.modelData.maxTempF + "\u00B0 / " + forecastDayItem.modelData.minTempF + "\u00B0" : forecastDayItem.modelData.maxTempC + "\u00B0 / " + forecastDayItem.modelData.minTempC + "\u00B0"
            font.weight: 600
            color: Colours.palette.m3tertiary
        }
    }
}
