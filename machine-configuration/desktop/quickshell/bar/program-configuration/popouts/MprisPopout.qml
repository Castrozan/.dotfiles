import Quickshell.Services.Mpris
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: mprisPopoutRoot

    property bool active: false

    readonly property MprisPlayer activePlayer: {
        let players = Mpris.players;
        let firstAvailable = null;
        for (let i = 0; i < players.count; i++) {
            let player = players.get(i);
            if (player.playbackState === MprisPlaybackState.Playing)
                return player;
            if (!firstAvailable)
                firstAvailable = player;
        }
        return firstAvailable;
    }

    spacing: 12

    Text {
        text: "Media"
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    ColumnLayout {
        spacing: 4
        visible: mprisPopoutRoot.activePlayer !== null

        Text {
            Layout.fillWidth: true
            text: mprisPopoutRoot.activePlayer ? mprisPopoutRoot.activePlayer.trackTitle : ""
            font.pixelSize: 13
            font.bold: true
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.foreground
            elide: Text.ElideRight
            maximumLineCount: 1
        }

        Text {
            Layout.fillWidth: true
            text: mprisPopoutRoot.activePlayer ? mprisPopoutRoot.activePlayer.trackArtist : ""
            font.pixelSize: 11
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.accent
            elide: Text.ElideRight
            maximumLineCount: 1
            visible: text !== ""
        }
    }

    Text {
        text: "No media playing"
        font.pixelSize: 12
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.dim
        visible: mprisPopoutRoot.activePlayer === null
    }

    Rectangle {
        Layout.fillWidth: true
        height: 1
        color: ThemeColors.surfaceTranslucent
        visible: mprisPopoutRoot.activePlayer !== null
    }

    RowLayout {
        spacing: 4
        visible: mprisPopoutRoot.activePlayer !== null

        MprisPopoutControlButton {
            iconText: "󰒮"
            isEnabled: mprisPopoutRoot.activePlayer ? mprisPopoutRoot.activePlayer.canGoPrevious : false
            onClicked: { if (mprisPopoutRoot.activePlayer) mprisPopoutRoot.activePlayer.previous(); }
        }

        MprisPopoutControlButton {
            iconText: mprisPopoutRoot.activePlayer && mprisPopoutRoot.activePlayer.playbackState === MprisPlaybackState.Playing ? "󰏤" : "󰐊"
            isEnabled: mprisPopoutRoot.activePlayer ? (mprisPopoutRoot.activePlayer.canPlay || mprisPopoutRoot.activePlayer.canPause) : false
            onClicked: { if (mprisPopoutRoot.activePlayer) mprisPopoutRoot.activePlayer.togglePlaying(); }
        }

        MprisPopoutControlButton {
            iconText: "󰒭"
            isEnabled: mprisPopoutRoot.activePlayer ? mprisPopoutRoot.activePlayer.canGoNext : false
            onClicked: { if (mprisPopoutRoot.activePlayer) mprisPopoutRoot.activePlayer.next(); }
        }

        Item { Layout.fillWidth: true }

        Text {
            text: mprisPopoutRoot.activePlayer ? mprisPopoutRoot.activePlayer.identity : ""
            font.pixelSize: 11
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.dim
            visible: text !== ""
        }
    }
}
