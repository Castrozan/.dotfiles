pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

import "../../widgets"
import "PlaybackDuration.js" as PlaybackDuration

ColumnLayout {
    id: detailsColumn

    required property real playerProgress

    readonly property int detailsColumnWidth: 220

    implicitWidth: detailsColumnWidth
    spacing: Appearance.spacing.small

    StyledText {
        Layout.fillWidth: true
        Layout.maximumWidth: parent.implicitWidth

        animate: true
        horizontalAlignment: Text.AlignHCenter
        text: (PlayersService.active?.trackTitle ?? "No media") || "Unknown title"
        color: PlayersService.active ? Colours.palette.m3primary : Colours.palette.m3onSurface
        font.pointSize: Appearance.font.size.normal
        elide: Text.ElideRight
    }

    StyledText {
        Layout.fillWidth: true
        Layout.maximumWidth: parent.implicitWidth

        animate: true
        horizontalAlignment: Text.AlignHCenter
        visible: !!PlayersService.active
        text: PlayersService.active?.trackAlbum || "Unknown album"
        color: Colours.palette.m3outline
        font.pointSize: Appearance.font.size.small
        elide: Text.ElideRight
    }

    StyledText {
        Layout.fillWidth: true
        Layout.maximumWidth: parent.implicitWidth

        animate: true
        horizontalAlignment: Text.AlignHCenter
        text: (PlayersService.active?.trackArtist ?? "Play some music for stuff to show up here!") || "Unknown artist"
        color: PlayersService.active ? Colours.palette.m3secondary : Colours.palette.m3outline
        elide: Text.ElideRight
        wrapMode: PlayersService.active ? Text.NoWrap : Text.WordWrap
    }

    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: Appearance.spacing.small
        Layout.bottomMargin: Appearance.spacing.smaller

        spacing: Appearance.spacing.small

        MediaPlayerControl {
            type: IconButton.Text
            icon: "skip_previous"
            font.pointSize: Math.round(Appearance.font.size.large * 1.5)
            disabled: !PlayersService.active?.canGoPrevious
            onClicked: PlayersService.active?.previous()
        }

        MediaPlayerControl {
            icon: PlayersService.active?.isPlaying ? "pause" : "play_arrow"
            label.animate: true
            toggle: true
            padding: Appearance.padding.small / 2
            checked: PlayersService.active?.isPlaying ?? false
            font.pointSize: Math.round(Appearance.font.size.large * 1.5)
            disabled: !PlayersService.active?.canTogglePlaying
            onClicked: PlayersService.active?.togglePlaying()
        }

        MediaPlayerControl {
            type: IconButton.Text
            icon: "skip_next"
            font.pointSize: Math.round(Appearance.font.size.large * 1.5)
            disabled: !PlayersService.active?.canGoNext
            onClicked: PlayersService.active?.next()
        }
    }

    StyledSlider {
        id: seekSlider

        Layout.fillWidth: true
        enabled: !!PlayersService.active
        implicitHeight: Appearance.padding.normal * 3

        onMoved: {
            const activePlayer = PlayersService.active;
            if (activePlayer?.canSeek && activePlayer?.positionSupported)
                activePlayer.position = value * activePlayer.length;
        }

        Binding {
            target: seekSlider
            property: "value"
            value: detailsColumn.playerProgress
            when: !seekSlider.pressed
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton

            onWheel: wheel => {
                const activePlayer = PlayersService.active;
                if (!activePlayer?.canSeek || !activePlayer?.positionSupported)
                    return;

                wheel.accepted = true;
                const seekDeltaSeconds = wheel.angleDelta.y > 0 ? 10 : -10;
                Qt.callLater(() => {
                    activePlayer.position = Math.max(0, Math.min(activePlayer.length, activePlayer.position + seekDeltaSeconds));
                });
            }
        }
    }

    Item {
        Layout.fillWidth: true
        implicitHeight: Math.max(positionLabel.implicitHeight, durationLabel.implicitHeight)

        StyledText {
            id: positionLabel

            anchors.left: parent.left
            text: PlaybackDuration.format(PlayersService.active?.position ?? -1)
            color: Colours.palette.m3onSurfaceVariant
            font.pointSize: Appearance.font.size.small
        }

        StyledText {
            id: durationLabel

            anchors.right: parent.right
            text: PlaybackDuration.format(PlayersService.active?.length ?? -1)
            color: Colours.palette.m3onSurfaceVariant
            font.pointSize: Appearance.font.size.small
        }
    }

    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        spacing: Appearance.spacing.small

        MediaPlayerControl {
            type: IconButton.Text
            icon: "move_up"
            inactiveOnColour: Colours.palette.m3secondary
            padding: Appearance.padding.small
            font.pointSize: Appearance.font.size.large
            disabled: !PlayersService.active?.canRaise
            onClicked: PlayersService.active?.raise()
        }

        PlayerSourceBadge {}

        MediaPlayerControl {
            type: IconButton.Text
            icon: "delete"
            inactiveOnColour: Colours.palette.m3error
            padding: Appearance.padding.small
            font.pointSize: Appearance.font.size.large
            disabled: !PlayersService.active?.canQuit
            onClicked: PlayersService.active?.quit()
        }
    }
}
