pragma Singleton

import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: themeColorsRoot

    readonly property string themeColorsPath: `${Quickshell.env("HOME")}/.config/hypr-theme/current/theme/quickshell-bar-colors.json`

    function parseThemeColors(jsonText: string): var {
        try {
            return JSON.parse(jsonText);
        } catch (error) {
            return null;
        }
    }

    function rgbStringToQtColor(rgbString: string, alpha: real): color {
        let parts = rgbString.split(",");
        if (parts.length !== 3) return Qt.rgba(0, 0, 0, alpha);
        return Qt.rgba(
            parseInt(parts[0].trim()) / 255.0,
            parseInt(parts[1].trim()) / 255.0,
            parseInt(parts[2].trim()) / 255.0,
            alpha
        );
    }

    readonly property var themeData: themeColorsFile.loaded ? parseThemeColors(themeColorsFile.text()) : null

    readonly property color background: themeData ? rgbStringToQtColor(themeData.backgroundRgb, 0.85) : Qt.rgba(0, 0, 0, 0.85)
    readonly property color backgroundSolid: themeData ? themeData.background : "#1e1e2e"
    readonly property color foreground: themeData ? themeData.foreground : "#cdd6f4"
    readonly property color accent: themeData ? themeData.accent : "#94e2d5"
    readonly property color warning: themeData ? themeData.warning : "#f9e2af"
    readonly property color error: themeData ? themeData.error : "#f38ba8"
    readonly property color secondary: themeData ? themeData.secondary : "#f5c2e7"
    readonly property color surface: themeData ? themeData.surface : "#45475a"
    readonly property color primary: themeData ? themeData.primary : "#89b4fa"
    readonly property color dim: themeData ? themeData.dim : "#6c7086"
    readonly property color backgroundTranslucent: themeData ? rgbStringToQtColor(themeData.backgroundRgb, 0.92) : Qt.rgba(0, 0, 0, 0.92)
    readonly property color surfaceTranslucent: themeData ? rgbStringToQtColor(themeData.surfaceRgb, 0.6) : Qt.rgba(0.3, 0.3, 0.3, 0.6)

    FileView {
        id: themeColorsFile
        path: Qt.url(`file://${themeColorsPath}`)
        watchChanges: true
        blockLoading: true
        onFileChanged: this.reload()
    }
}
