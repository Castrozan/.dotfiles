pragma Singleton

import ".."
import Quickshell
import QtQuick

Singleton {
    id: coloursRoot

    readonly property var palette: QtObject {
        readonly property color m3surface: ThemeColors.backgroundSolid
        readonly property color m3onSurface: ThemeColors.foreground
        readonly property color m3primary: ThemeColors.accent
        readonly property color m3onPrimary: ThemeColors.backgroundSolid
        readonly property color m3secondary: ThemeColors.secondary
        readonly property color m3onSecondary: ThemeColors.backgroundSolid
        readonly property color m3secondaryContainer: Qt.alpha(ThemeColors.secondary, 0.2)
        readonly property color m3onSecondaryContainer: ThemeColors.secondary
        readonly property color m3tertiary: ThemeColors.primary
        readonly property color m3surfaceContainer: Qt.lighter(ThemeColors.backgroundSolid, 1.15)
        readonly property color m3surfaceContainerHigh: Qt.lighter(ThemeColors.backgroundSolid, 1.2)
        readonly property color m3surfaceContainerHighest: Qt.lighter(ThemeColors.backgroundSolid, 1.25)
        readonly property color m3onSurfaceVariant: ThemeColors.dim
        readonly property color m3outline: ThemeColors.dim
        readonly property color m3outlineVariant: Qt.alpha(ThemeColors.dim, 0.3)
        readonly property color m3error: ThemeColors.error
        readonly property color m3scrim: Qt.alpha("#000000", 0.35)
    }

    readonly property var tPalette: QtObject {
        readonly property color m3surfaceContainer: Qt.lighter(ThemeColors.backgroundSolid, 1.15)
        readonly property color m3surfaceContainerHigh: Qt.lighter(ThemeColors.backgroundSolid, 1.2)
    }

    function layer(baseColor: color, level: int): color {
        return Qt.lighter(baseColor, 1 + level * 0.05);
    }
}
