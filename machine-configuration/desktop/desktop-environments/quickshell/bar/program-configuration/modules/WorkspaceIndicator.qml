import QtQuick
import ".."

Rectangle {
    id: workspaceIndicatorRoot

    required property int workspaceId
    required property bool isActive
    required property bool isOccupied
    required property bool useWarningColor

    readonly property color activeBackground: useWarningColor ? ThemeColors.warning : ThemeColors.accent
    readonly property color occupiedTextColor: useWarningColor ? ThemeColors.warning : ThemeColors.accent
    readonly property color emptyTextColor: useWarningColor ? ThemeColors.warning : ThemeColors.foreground

    width: 28
    height: 28
    radius: 14
    color: {
        if (isActive) return activeBackground;
        return "transparent";
    }
    border.width: useWarningColor && !isActive ? 1.5 : 0
    border.color: ThemeColors.warning

    Text {
        anchors.centerIn: parent
        text: workspaceId
        font.pixelSize: 13
        font.bold: workspaceIndicatorRoot.isActive || workspaceIndicatorRoot.isOccupied || workspaceIndicatorRoot.useWarningColor
        font.family: "JetBrainsMono Nerd Font"
        color: {
            if (isActive) return ThemeColors.backgroundSolid;
            if (isOccupied) return occupiedTextColor;
            return emptyTextColor;
        }
    }

    Behavior on color {
        ColorAnimation { duration: 150 }
    }
}
