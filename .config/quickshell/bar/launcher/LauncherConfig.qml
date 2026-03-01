pragma Singleton

import Quickshell
import QtQuick

Singleton {
    readonly property int contentWidth: 520
    readonly property int maxVisibleItems: 7
    readonly property int searchBarHeight: 48
    readonly property int itemHeight: 48
    readonly property int wallpaperThumbnailSize: 120
    readonly property string actionPrefix: ">"
    readonly property string themePrefix: ">scheme "
    readonly property string wallpaperPrefix: ">wallpaper "
}
