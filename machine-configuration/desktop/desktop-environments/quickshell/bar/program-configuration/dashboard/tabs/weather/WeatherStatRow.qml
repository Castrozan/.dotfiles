pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

Row {
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
