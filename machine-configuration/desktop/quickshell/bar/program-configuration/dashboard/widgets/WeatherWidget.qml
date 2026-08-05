pragma ComponentBehavior: Bound

import "../components"
import "../services"
import ".."
import QtQuick

Item {
    id: weatherWidgetRoot

    anchors.centerIn: parent

    implicitWidth: weatherIcon.implicitWidth + weatherInfoColumn.implicitWidth + weatherInfoColumn.anchors.leftMargin

    MaterialIcon {
        id: weatherIcon

        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left

        animate: true
        text: WeatherService.icon
        color: Colours.palette.m3secondary
        font.pointSize: Appearance.font.size.extraLarge * 2
    }

    Column {
        id: weatherInfoColumn

        anchors.verticalCenter: parent.verticalCenter
        anchors.left: weatherIcon.right
        anchors.leftMargin: Appearance.spacing.large

        spacing: Appearance.spacing.small

        StyledText {
            anchors.horizontalCenter: parent.horizontalCenter

            animate: true
            text: WeatherService.temperature
            color: Colours.palette.m3primary
            font.pointSize: Appearance.font.size.extraLarge
            font.weight: 500
        }

        StyledText {
            anchors.horizontalCenter: parent.horizontalCenter

            animate: true
            text: WeatherService.description

            elide: Text.ElideRight
            width: Math.min(implicitWidth, weatherWidgetRoot.parent.width - weatherIcon.implicitWidth - weatherInfoColumn.anchors.leftMargin - Appearance.padding.large * 2)
        }
    }
}
