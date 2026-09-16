pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

RowLayout {
    property string iconName
    property string title

    Layout.fillWidth: true
    spacing: Appearance.spacing.small

    MaterialIcon {
        text: parent.iconName
        fill: 1
        color: Colours.palette.m3primary
        font.pointSize: Appearance.font.size.large
    }

    StyledText {
        Layout.fillWidth: true
        text: parent.title
        font.pointSize: Appearance.font.size.normal
        font.weight: Font.Medium
        color: Colours.palette.m3onSurface
    }
}
