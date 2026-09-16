import Quickshell
import Quickshell.Io
import QtQuick

Scope {
    id: switcherTheme
    readonly property string themeColorsPath: `${Quickshell.env("HOME")}/.config/hypr-theme/current/theme/quickshell-osd-colors.json`

    function parseThemeColors(jsonText: string): var {
        try {
            return JSON.parse(jsonText);
        } catch (error) {
            return null;
        }
    }

    function rgbStringToQtColor(rgbString: string, alpha: real): color {
        let parts = rgbString.split(",");
        if (parts.length !== 3)
            return Qt.rgba(0, 0, 0, alpha);
        return Qt.rgba(parseInt(parts[0].trim()) / 255.0, parseInt(parts[1].trim()) / 255.0, parseInt(parts[2].trim()) / 255.0, alpha);
    }

    readonly property var themeColors: themeColorsFile.loaded ? parseThemeColors(themeColorsFile.text()) : null

    readonly property color themeBackground: themeColors ? rgbStringToQtColor(themeColors.backgroundRgb, 0.85) : Qt.rgba(0.1, 0.1, 0.1, 0.85)
    readonly property color themeForeground: themeColors ? themeColors.foreground : "white"
    readonly property color themeAccent: themeColors ? themeColors.accent : "#89b4fa"
    readonly property color themeDimOverlay: Qt.rgba(0, 0, 0, 0.25)

    FileView {
        id: themeColorsFile
        path: Qt.url(`file://${switcherTheme.themeColorsPath}`)
        watchChanges: true
        blockLoading: true
        onFileChanged: this.reload()
    }
}
