pragma ComponentBehavior: Bound

import "../../dashboard/components"
import "../../dashboard"
import "../.."
import QtQuick

StyledRect {
    id: launcherThemeItemRoot

    required property var themeData
    property bool isCurrentTheme: false
    property bool isCurrentItem: false

    signal activated

    implicitHeight: 48
    radius: Appearance.rounding.normal
    color: isCurrentItem ? Colours.palette.m3secondaryContainer : "transparent"

    Row {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Appearance.padding.normal
        spacing: Appearance.spacing.normal

        Item {
            width: 28
            height: 28
            anchors.verticalCenter: parent.verticalCenter

            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: launcherThemeItemRoot.themeData.background
                border.width: 1
                border.color: Colours.palette.m3outlineVariant

                Rectangle {
                    width: parent.width / 2
                    height: parent.height
                    anchors.right: parent.right
                    radius: parent.radius
                    color: launcherThemeItemRoot.themeData.accent

                    Rectangle {
                        anchors.left: parent.left
                        width: parent.width / 2
                        height: parent.height
                        color: launcherThemeItemRoot.themeData.accent
                    }
                }
            }
        }

        StyledText {
            anchors.verticalCenter: parent.verticalCenter
            text: launcherThemeItemRoot.themeData.name
            font.pointSize: Appearance.font.size.normal
            color: launcherThemeItemRoot.isCurrentItem ? Colours.palette.m3onSecondaryContainer : Colours.palette.m3onSurface
        }
    }

    MaterialIcon {
        anchors.right: parent.right
        anchors.rightMargin: Appearance.padding.normal
        anchors.verticalCenter: parent.verticalCenter
        visible: launcherThemeItemRoot.isCurrentTheme
        text: "check"
        color: Colours.palette.m3primary
    }

    StateLayer {
        radius: launcherThemeItemRoot.radius

        function onClicked(): void {
            launcherThemeItemRoot.activated();
        }
    }
}
