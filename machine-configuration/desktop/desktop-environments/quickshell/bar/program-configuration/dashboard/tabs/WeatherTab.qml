pragma ComponentBehavior: Bound

import "../components"
import "weather"
import "../services"
import ".."
import QtQuick
import QtQuick.Layouts

Item {
    id: weatherTabRoot

    implicitWidth: weatherLayout.implicitWidth > 800 ? weatherLayout.implicitWidth : 840
    implicitHeight: weatherLayout.implicitHeight

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
                    text: new Date().toLocaleDateString(Qt.locale("en_US"), "dddd, MMMM d")
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

                    WeatherForecastDay {}
                }
            }
        }
    }
}
