import Quickshell.Services.Mpris
import QtQuick
import QtQuick.Layouts

RowLayout {
    id: playbackControlsRowRoot

    property MprisPlayer activePlayer: null

    spacing: 8

    PlaybackControlButton {
        iconText: "󰒮"
        isEnabled: playbackControlsRowRoot.activePlayer ? playbackControlsRowRoot.activePlayer.canGoPrevious : false
        onClicked: {
            if (playbackControlsRowRoot.activePlayer)
                playbackControlsRowRoot.activePlayer.previous();
        }
    }

    PlaybackControlButton {
        iconText: {
            if (!playbackControlsRowRoot.activePlayer) return "󰐊";
            return playbackControlsRowRoot.activePlayer.playbackState === MprisPlaybackState.Playing ? "󰏤" : "󰐊";
        }
        isEnabled: {
            if (!playbackControlsRowRoot.activePlayer) return false;
            return playbackControlsRowRoot.activePlayer.canPlay || playbackControlsRowRoot.activePlayer.canPause;
        }
        onClicked: {
            if (playbackControlsRowRoot.activePlayer)
                playbackControlsRowRoot.activePlayer.togglePlaying();
        }
    }

    PlaybackControlButton {
        iconText: "󰒭"
        isEnabled: playbackControlsRowRoot.activePlayer ? playbackControlsRowRoot.activePlayer.canGoNext : false
        onClicked: {
            if (playbackControlsRowRoot.activePlayer)
                playbackControlsRowRoot.activePlayer.next();
        }
    }
}
