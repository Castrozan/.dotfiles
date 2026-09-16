pragma ComponentBehavior: Bound

import "../../components"
import "../.."
import QtQuick
import QtQuick.Layouts

StyledRect {
    id: performanceGaugeCardRoot

    property string iconName
    property string title
    property real percentage: 0
    property string subtitle
    property color accentColor: Colours.palette.m3primary
    property real animatedPercentage: 0

    color: Colours.tPalette.m3surfaceContainer
    radius: Appearance.rounding.large
    clip: true
    Component.onCompleted: animatedPercentage = percentage
    onPercentageChanged: animatedPercentage = percentage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Appearance.padding.large
        spacing: Appearance.spacing.smaller

        PerformanceCardHeader {
            iconName: performanceGaugeCardRoot.iconName
            title: performanceGaugeCardRoot.title
            accentColor: performanceGaugeCardRoot.accentColor
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            PerformanceGaugeArc {
                anchors.centerIn: parent
                width: Math.min(parent.width, parent.height)
                height: width
                percentage: performanceGaugeCardRoot.animatedPercentage
                accentColor: performanceGaugeCardRoot.accentColor
            }

            StyledText {
                anchors.centerIn: parent
                text: `${Math.round(performanceGaugeCardRoot.percentage * 100)}%`
                font.pointSize: Appearance.font.size.extraLarge
                font.weight: Font.Medium
                color: performanceGaugeCardRoot.accentColor
            }
        }

        StyledText {
            Layout.alignment: Qt.AlignHCenter
            text: performanceGaugeCardRoot.subtitle
            font.pointSize: Appearance.font.size.smaller
            color: Colours.palette.m3onSurfaceVariant
        }
    }

    Behavior on animatedPercentage {
        Anim {
            duration: Appearance.anim.durations.large
        }
    }
}
