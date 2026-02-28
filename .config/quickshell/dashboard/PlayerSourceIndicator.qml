import Quickshell.Services.Mpris
import QtQuick

Rectangle {
    id: playerSourceIndicatorRoot

    property MprisPlayer activePlayer: null

    readonly property string playerIdentity: activePlayer ? activePlayer.identity : ""

    width: playerSourceLabel.implicitWidth + 16
    height: 22
    radius: 11
    color: ThemeColors.surfaceTranslucent
    visible: playerIdentity !== ""

    Text {
        id: playerSourceLabel
        anchors.centerIn: parent
        text: playerSourceIndicatorRoot.playerIdentity
        font.pixelSize: 10
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.dim
    }
}
