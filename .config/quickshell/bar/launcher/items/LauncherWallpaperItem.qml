pragma ComponentBehavior: Bound

import "../../dashboard/components"
import "../../dashboard"
import "../.."
import ".."
import QtQuick

StyledClippingRect {
    id: launcherWallpaperItemRoot

    required property var wallpaperData
    property bool isCurrentWallpaper: false
    property bool isCurrentItem: false

    signal activated

    implicitWidth: LauncherConfig.wallpaperThumbnailSize
    implicitHeight: LauncherConfig.wallpaperThumbnailSize * 0.65 + wallpaperNameLabel.implicitHeight + Appearance.spacing.small

    radius: Appearance.rounding.normal
    color: isCurrentItem ? Colours.palette.m3secondaryContainer : "transparent"

    Column {
        anchors.fill: parent
        anchors.margins: Appearance.padding.smaller
        spacing: Appearance.spacing.small

        StyledClippingRect {
            width: parent.width
            height: LauncherConfig.wallpaperThumbnailSize * 0.65 - Appearance.padding.smaller
            radius: Appearance.rounding.small

            Image {
                anchors.fill: parent
                source: `file://${launcherWallpaperItemRoot.wallpaperData.path}`
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
            }

            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.width: launcherWallpaperItemRoot.isCurrentWallpaper ? 2 : 0
                border.color: Colours.palette.m3primary
                radius: parent.radius
            }
        }

        StyledText {
            id: wallpaperNameLabel

            width: parent.width
            text: launcherWallpaperItemRoot.wallpaperData.name
            font.pointSize: Appearance.font.size.smaller
            color: Colours.palette.m3onSurfaceVariant
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignHCenter
        }
    }

    StateLayer {
        radius: launcherWallpaperItemRoot.radius

        function onClicked(): void {
            launcherWallpaperItemRoot.activated();
        }
    }
}
