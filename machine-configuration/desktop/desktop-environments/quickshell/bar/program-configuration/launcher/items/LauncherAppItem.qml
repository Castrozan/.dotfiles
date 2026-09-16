pragma ComponentBehavior: Bound

import "../../dashboard/components"
import "../../dashboard"
import "../.."
import QtQuick

StyledRect {
    id: launcherAppItemRoot

    required property var desktopEntry
    readonly property string appName: desktopEntry?.name ?? ""
    readonly property string appIcon: desktopEntry?.icon ?? ""
    readonly property string appGenericName: desktopEntry?.genericName ?? ""
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

        Item {
            width: 32
            height: 32
            anchors.verticalCenter: parent.verticalCenter

            Image {
                anchors.fill: parent
                source: launcherAppItemRoot.appIcon
                    ? `image://icon/${launcherAppItemRoot.appIcon}`
                    : ""
                sourceSize: Qt.size(32, 32)
                visible: launcherAppItemRoot.appIcon !== ""
            }

            MaterialIcon {
                anchors.centerIn: parent
                text: "apps"
                visible: launcherAppItemRoot.appIcon === ""
                color: Colours.palette.m3onSurfaceVariant
            }
        }

        Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2

            StyledText {
                text: launcherAppItemRoot.appName
                font.pointSize: Appearance.font.size.normal
                color: launcherAppItemRoot.isCurrentItem ? Colours.palette.m3onSecondaryContainer : Colours.palette.m3onSurface
            }

            StyledText {
                visible: text !== ""
                text: launcherAppItemRoot.appGenericName
                font.pointSize: Appearance.font.size.smaller
                color: Colours.palette.m3onSurfaceVariant
            }
        }
    }

    StateLayer {
        radius: launcherAppItemRoot.radius

        function onClicked(): void {
            launcherAppItemRoot.activated();
        }
    }
}
