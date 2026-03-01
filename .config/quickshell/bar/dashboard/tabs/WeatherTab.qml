pragma ComponentBehavior: Bound

import "../components"
import "../services"
import ".."
import QtQuick
import QtQuick.Layouts

Item {
    id: weatherTabRoot

    implicitWidth: weatherLayout.implicitWidth > 800 ? weatherLayout.implicitWidth : 840
    implicitHeight: weatherLayout.implicitHeight

    Component.onCompleted: WeatherService.reload()

    ColumnLayout {
        id: weatherLayout

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Appearance.spacing.smaller

        RowLayout {
            Layout.leftMargin: Appearance.padding.large
            Layout.rightMargin: Appearance.padding.large
            Layout.fillWidth: true

            Column {
                spacing: Appearance.spacing.small / 2

                StyledText {
                    text: WeatherService.city || "Loading..."
                    font.pointSize: Appearance.font.size.extraLarge
                    font.weight: 600
                    color: Colours.palette.m3onSurface
                }

                StyledText {
                    text: new Date().toLocaleDateString(Qt.locale(), "dddd, MMMM d")
                    font.pointSize: Appearance.font.size.small
                    color: Colours.palette.m3onSurfaceVariant
                }
            }

            Item {
                Layout.fillWidth: true
            }

            Row {
                spacing: Appearance.spacing.large

                WeatherStatRow {
                    iconName: "wb_twilight"
                    label: "Sunrise"
                    value: WeatherService.sunrise
                    statColour: Colours.palette.m3tertiary
                }

                WeatherStatRow {
                    iconName: "bedtime"
                    label: "Sunset"
                    value: WeatherService.sunset
                    statColour: Colours.palette.m3tertiary
                }
            }
        }

        StyledRect {
            Layout.fillWidth: true
            implicitHeight: currentConditionsRow.implicitHeight + Appearance.padding.small * 2

            radius: Appearance.rounding.large * 2
            color: Colours.tPalette.m3surfaceContainer

            RowLayout {
                id: currentConditionsRow

                anchors.centerIn: parent
                spacing: Appearance.spacing.large

                MaterialIcon {
                    Layout.alignment: Qt.AlignVCenter
                    text: WeatherService.icon
                    font.pointSize: Appearance.font.size.extraLarge * 3
                    color: Colours.palette.m3secondary
                    animate: true
                }

                ColumnLayout {
                    Layout.alignment: Qt.AlignVCenter
                    spacing: -Appearance.spacing.small

                    StyledText {
                        text: WeatherService.temperature
                        font.pointSize: Appearance.font.size.extraLarge * 2
                        font.weight: 500
                        color: Colours.palette.m3primary
                    }

                    StyledText {
                        Layout.leftMargin: Appearance.padding.small
                        text: WeatherService.description
                        font.pointSize: Appearance.font.size.normal
                        color: Colours.palette.m3onSurfaceVariant
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Appearance.spacing.smaller

            WeatherDetailCard {
                iconName: "water_drop"
                label: "Humidity"
                value: WeatherService.humidity + "%"
                cardColour: Colours.palette.m3secondary
            }
            WeatherDetailCard {
                iconName: "thermostat"
                label: "Feels Like"
                value: WeatherService.feelsLikeTemperature
                cardColour: Colours.palette.m3primary
            }
            WeatherDetailCard {
                iconName: "air"
                label: "Wind"
                value: WeatherService.windSpeed ? WeatherService.windSpeed + " km/h" : "--"
                cardColour: Colours.palette.m3tertiary
            }
        }

        StyledText {
            Layout.topMargin: Appearance.spacing.normal
            Layout.leftMargin: Appearance.padding.normal
            visible: forecastRepeater.count > 0
            text: "7-Day Forecast"
            font.pointSize: Appearance.font.size.normal
            font.weight: 600
            color: Colours.palette.m3onSurface
        }

        Item {
            Layout.fillWidth: true
            implicitHeight: forecastRowLayout.implicitHeight

            RowLayout {
                id: forecastRowLayout

                anchors.left: parent.left
                anchors.right: parent.right
                spacing: Appearance.spacing.smaller

                Repeater {
                    id: forecastRepeater

                    model: WeatherService.forecast

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
                                text: forecastDayItem.index === 0 ? "Today" : new Date(forecastDayItem.modelData.date).toLocaleDateString(Qt.locale(), "ddd")
                                font.pointSize: Appearance.font.size.normal
                                font.weight: 600
                                color: Colours.palette.m3primary
                            }

                            StyledText {
                                Layout.topMargin: -Appearance.spacing.small / 2
                                Layout.alignment: Qt.AlignHCenter
                                text: new Date(forecastDayItem.modelData.date).toLocaleDateString(Qt.locale(), "MMM d")
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
                                text: DashboardConfig.useFahrenheit
                                    ? forecastDayItem.modelData.maxTempF + "\u00B0 / " + forecastDayItem.modelData.minTempF + "\u00B0"
                                    : forecastDayItem.modelData.maxTempC + "\u00B0 / " + forecastDayItem.modelData.minTempC + "\u00B0"
                                font.weight: 600
                                color: Colours.palette.m3tertiary
                            }
                        }
                    }
                }
            }
        }
    }

    component WeatherDetailCard: StyledRect {
        id: weatherDetailCardRoot

        property string iconName
        property string label
        property string value
        property color cardColour

        Layout.fillWidth: true
        Layout.preferredHeight: 60
        radius: Appearance.rounding.small
        color: Colours.tPalette.m3surfaceContainer

        Row {
            anchors.centerIn: parent
            spacing: Appearance.spacing.normal

            MaterialIcon {
                text: weatherDetailCardRoot.iconName
                color: weatherDetailCardRoot.cardColour
                font.pointSize: Appearance.font.size.large
                anchors.verticalCenter: parent.verticalCenter
            }

            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0

                StyledText {
                    text: weatherDetailCardRoot.label
                    font.pointSize: Appearance.font.size.smaller
                    opacity: 0.7
                    horizontalAlignment: Text.AlignLeft
                }
                StyledText {
                    text: weatherDetailCardRoot.value
                    font.weight: 600
                    horizontalAlignment: Text.AlignLeft
                }
            }
        }
    }

    component WeatherStatRow: Row {
        id: weatherStatRowRoot

        property string iconName
        property string label
        property string value
        property color statColour

        spacing: Appearance.spacing.small

        MaterialIcon {
            text: weatherStatRowRoot.iconName
            font.pointSize: Appearance.font.size.extraLarge
            color: weatherStatRowRoot.statColour
        }

        Column {
            StyledText {
                text: weatherStatRowRoot.label
                font.pointSize: Appearance.font.size.smaller
                color: Colours.palette.m3onSurfaceVariant
            }
            StyledText {
                text: weatherStatRowRoot.value
                font.pointSize: Appearance.font.size.small
                font.weight: 600
                color: Colours.palette.m3onSurface
            }
        }
    }
}
