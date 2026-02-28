import Quickshell.Hyprland
import QtQuick
import ".."

Item {
    id: activeWindowModuleRoot

    clip: true

    readonly property string windowTitle: Hyprland.focusedToplevel ? (Hyprland.focusedToplevel.title || "Desktop") : "Desktop"

    Text {
        anchors.centerIn: parent
        rotation: 90
        width: activeWindowModuleRoot.height
        text: windowTitle
        font.pixelSize: 11
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.dim
        elide: Text.ElideRight
        horizontalAlignment: Text.AlignHCenter
    }
}
