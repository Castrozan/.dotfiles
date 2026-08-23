pragma ComponentBehavior: Bound

import "../../components"
import "../.."
import QtQuick
import QtQuick.Layouts

StyledRect {
    id: performanceHeroCardRoot

    property string iconName
    property string title
    property string mainValue
    property string mainLabel
    property string secondaryValue
    property string secondaryLabel
    property real usage: 0
    property real temperature: 0
    property color accentColor: Colours.palette.m3primary
    readonly property real maximumTemperature: 100
    readonly property real temperatureProgress: Math.min(1, Math.max(0, temperature / maximumTemperature))
    property real animatedUsage: 0
    property real animatedTemperature: 0

    color: Colours.tPalette.m3surfaceContainer
    radius: Appearance.rounding.large
    clip: true
    Component.onCompleted: {
        animatedUsage = usage;
        animatedTemperature = temperatureProgress;
    }
    onUsageChanged: animatedUsage = usage
    onTemperatureProgressChanged: animatedTemperature = temperatureProgress

    StyledRect {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: parent.width * performanceHeroCardRoot.animatedUsage
        color: Qt.alpha(performanceHeroCardRoot.accentColor, 0.15)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: Appearance.padding.large
        anchors.leftMargin: Appearance.padding.large
        anchors.rightMargin: Appearance.padding.large
        anchors.bottomMargin: Appearance.padding.normal
        spacing: Appearance.spacing.small

        PerformanceCardHeader {
            iconName: performanceHeroCardRoot.iconName
            title: performanceHeroCardRoot.title
            accentColor: performanceHeroCardRoot.accentColor
        }

        RowLayout {
            spacing: Appearance.spacing.normal

            Column {
                Layout.alignment: Qt.AlignBottom
                Layout.fillWidth: true
                spacing: Appearance.spacing.small

                Row {
                    spacing: Appearance.spacing.small

                    StyledText {
                        text: performanceHeroCardRoot.secondaryValue
                        font.pointSize: Appearance.font.size.normal
                        font.weight: Font.Medium
                    }

                    StyledText {
                        text: performanceHeroCardRoot.secondaryLabel
                        font.pointSize: Appearance.font.size.small
                        color: Colours.palette.m3onSurfaceVariant
                        anchors.baseline: parent.children[0].baseline
                    }
                }

                PerformanceProgressBar {
                    width: parent.width * 0.5
                    height: 6
                    value: performanceHeroCardRoot.temperatureProgress
                    foregroundColor: performanceHeroCardRoot.accentColor
                    backgroundColor: Qt.alpha(performanceHeroCardRoot.accentColor, 0.2)
                }
            }

            Item {
                Layout.fillWidth: true
            }
        }
    }

    Column {
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.margins: Appearance.padding.large
        anchors.rightMargin: 32
        spacing: 0

        StyledText {
            anchors.right: parent.right
            text: performanceHeroCardRoot.mainLabel
            font.pointSize: Appearance.font.size.normal
            color: Colours.palette.m3onSurfaceVariant
        }

        StyledText {
            anchors.right: parent.right
            text: performanceHeroCardRoot.mainValue
            font.pointSize: Appearance.font.size.extraLarge
            font.weight: Font.Medium
            color: performanceHeroCardRoot.accentColor
        }
    }

    Behavior on animatedUsage {
        Anim {
            duration: Appearance.anim.durations.large
        }
    }

    Behavior on animatedTemperature {
        Anim {
            duration: Appearance.anim.durations.large
        }
    }
}
