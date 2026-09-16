pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

StyledRect {
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
