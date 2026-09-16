pragma ComponentBehavior: Bound

import "../../components"
import "../.."
import QtQuick
import QtQuick.Layouts

RowLayout {
    id: performanceCardHeaderRoot

    property string iconName
    property string title
    property color accentColor: Colours.palette.m3primary

    Layout.fillWidth: true
    spacing: Appearance.spacing.small

    MaterialIcon {
        text: performanceCardHeaderRoot.iconName
        fill: 1
        color: performanceCardHeaderRoot.accentColor
        font.pointSize: Appearance.spacing.large
    }

    StyledText {
        Layout.fillWidth: true
        text: performanceCardHeaderRoot.title
        font.pointSize: Appearance.font.size.normal
        elide: Text.ElideRight
    }
}
