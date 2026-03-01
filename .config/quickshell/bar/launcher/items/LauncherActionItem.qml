pragma ComponentBehavior: Bound

import "../../dashboard/components"
import "../../dashboard"
import "../.."
import QtQuick

StyledRect {
    id: launcherActionItemRoot

    required property var actionData
    property bool isCurrentItem: false

    signal activated

    implicitHeight: 48
    radius: Appearance.rounding.normal
    color: isCurrentItem ? Colours.palette.m3secondaryContainer : "transparent"

    Row {
        anchors.fill: parent
        anchors.leftMargin: Appearance.padding.normal
        anchors.rightMargin: Appearance.padding.normal
        spacing: Appearance.spacing.normal

        MaterialIcon {
            anchors.verticalCenter: parent.verticalCenter
            text: launcherActionItemRoot.actionData.icon
            color: launcherActionItemRoot.isCurrentItem ? Colours.palette.m3onSecondaryContainer : Colours.palette.m3primary
        }

        Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2

            StyledText {
                text: launcherActionItemRoot.actionData.name
                font.pointSize: Appearance.font.size.normal
                color: launcherActionItemRoot.isCurrentItem ? Colours.palette.m3onSecondaryContainer : Colours.palette.m3onSurface
            }

            StyledText {
                text: launcherActionItemRoot.actionData.description
                font.pointSize: Appearance.font.size.smaller
                color: Colours.palette.m3onSurfaceVariant
            }
        }
    }

    StateLayer {
        radius: launcherActionItemRoot.radius

        function onClicked(): void {
            launcherActionItemRoot.activated();
        }
    }
}
