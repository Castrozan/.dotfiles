import Quickshell.Services.Mpris
import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: seekProgressBarRoot

    property MprisPlayer activePlayer: null
    property int positionPolled: 0

    readonly property int currentPositionMs: positionPolled
    readonly property int trackLengthMs: activePlayer ? activePlayer.length : 0
    readonly property real seekFraction: trackLengthMs > 0 ? Math.min(currentPositionMs / trackLengthMs, 1.0) : 0

    onActivePlayerChanged: {
        if (activePlayer)
            positionPolled = activePlayer.position;
        else
            positionPolled = 0;
    }

    spacing: 4

    function formatMillisecondsAsTime(milliseconds: int): string {
        let totalSeconds = Math.floor(milliseconds / 1000);
        let minutes = Math.floor(totalSeconds / 60);
        let seconds = totalSeconds % 60;
        return minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
    }

    Rectangle {
        Layout.fillWidth: true
        height: 6
        radius: 3
        color: ThemeColors.surfaceTranslucent

        Rectangle {
            width: parent.width * seekProgressBarRoot.seekFraction
            height: parent.height
            radius: 3
            color: ThemeColors.accent

            Behavior on width {
                NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: seekProgressBarRoot.activePlayer && seekProgressBarRoot.activePlayer.canSeek ? Qt.PointingHandCursor : Qt.ArrowCursor
            onClicked: function(mouse) {
                if (!seekProgressBarRoot.activePlayer || !seekProgressBarRoot.activePlayer.canSeek) return;
                let fraction = mouse.x / width;
                let targetPositionMs = Math.floor(fraction * seekProgressBarRoot.trackLengthMs);
                seekProgressBarRoot.activePlayer.position = targetPositionMs;
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true

        Text {
            text: seekProgressBarRoot.formatMillisecondsAsTime(seekProgressBarRoot.currentPositionMs)
            font.pixelSize: 10
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.dim
        }

        Item { Layout.fillWidth: true }

        Text {
            text: seekProgressBarRoot.formatMillisecondsAsTime(seekProgressBarRoot.trackLengthMs)
            font.pixelSize: 10
            font.family: "JetBrainsMono Nerd Font"
            color: ThemeColors.dim
        }
    }

    Timer {
        interval: 500
        running: seekProgressBarRoot.activePlayer !== null && seekProgressBarRoot.activePlayer.playbackState === MprisPlaybackState.Playing
        repeat: true
        onTriggered: {
            if (seekProgressBarRoot.activePlayer)
                seekProgressBarRoot.positionPolled = seekProgressBarRoot.activePlayer.position;
        }
    }
}
