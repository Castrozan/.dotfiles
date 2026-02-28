pragma ComponentBehavior: Bound

import "../components"
import "../services"
import ".."
import QtQuick

Item {
    id: mediaWidgetRoot

    property real playerProgress: {
        const activePlayer = PlayersService.active;
        return activePlayer?.length ? activePlayer.position / activePlayer.length : 0;
    }

    anchors.top: parent.top
    anchors.bottom: parent.bottom
    implicitWidth: DashboardConfig.sizes.mediaCoverArtSize + Appearance.padding.large * 2

    Behavior on playerProgress {
        Anim {
            duration: Appearance.anim.durations.large
        }
    }

    Timer {
        running: PlayersService.active?.isPlaying ?? false
        interval: DashboardConfig.mediaUpdateInterval
        triggeredOnStart: true
        repeat: true
        onTriggered: PlayersService.active?.positionChanged()
    }

    StyledClippingRect {
        id: coverArtContainer

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: Appearance.padding.large

        implicitHeight: width
        color: Colours.tPalette.m3surfaceContainerHigh
        radius: Infinity

        MaterialIcon {
            anchors.centerIn: parent
            grade: 200
            text: "art_track"
            color: Colours.palette.m3onSurfaceVariant
            font.pointSize: (parent.width * 0.4) || 1
        }

        Image {
            anchors.fill: parent
            source: PlayersService.active?.trackArtUrl ?? ""
            asynchronous: true
            fillMode: Image.PreserveAspectCrop
            sourceSize.width: width
            sourceSize.height: height
        }
    }

    Item {
        id: progressBarContainer

        anchors.top: coverArtContainer.bottom
        anchors.left: coverArtContainer.left
        anchors.right: coverArtContainer.right
        anchors.topMargin: Appearance.spacing.small

        height: 3

        Rectangle {
            anchors.fill: parent
            radius: height / 2
            color: Colours.layer(Colours.palette.m3surfaceContainerHigh, 2)

            Behavior on color {
                CAnim {}
            }
        }

        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.bottom: parent.bottom

            width: parent.width * mediaWidgetRoot.playerProgress
            radius: height / 2
            color: Colours.palette.m3primary

            Behavior on color {
                CAnim {}
            }
        }
    }

    StyledText {
        id: trackTitleLabel

        anchors.top: progressBarContainer.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: Appearance.spacing.small

        animate: true
        horizontalAlignment: Text.AlignHCenter
        text: (PlayersService.active?.trackTitle ?? "No media") || "Unknown title"
        color: Colours.palette.m3primary
        font.pointSize: Appearance.font.size.normal

        width: parent.implicitWidth - Appearance.padding.large * 2
        elide: Text.ElideRight
    }

    StyledText {
        id: trackAlbumLabel

        anchors.top: trackTitleLabel.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: Appearance.spacing.small

        animate: true
        horizontalAlignment: Text.AlignHCenter
        text: (PlayersService.active?.trackAlbum ?? "No media") || "Unknown album"
        color: Colours.palette.m3outline
        font.pointSize: Appearance.font.size.small

        width: parent.implicitWidth - Appearance.padding.large * 2
        elide: Text.ElideRight
    }

    StyledText {
        id: trackArtistLabel

        anchors.top: trackAlbumLabel.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: Appearance.spacing.small

        animate: true
        horizontalAlignment: Text.AlignHCenter
        text: (PlayersService.active?.trackArtist ?? "No media") || "Unknown artist"
        color: Colours.palette.m3secondary

        width: parent.implicitWidth - Appearance.padding.large * 2
        elide: Text.ElideRight
    }

    Row {
        id: mediaControlsRow

        anchors.top: trackArtistLabel.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: Appearance.spacing.smaller

        spacing: Appearance.spacing.small

        MediaControlButton {
            iconName: "skip_previous"
            canUse: PlayersService.active?.canGoPrevious ?? false

            function onClicked(): void {
                PlayersService.active?.previous();
            }
        }

        MediaControlButton {
            iconName: PlayersService.active?.isPlaying ? "pause" : "play_arrow"
            canUse: PlayersService.active?.canTogglePlaying ?? false

            function onClicked(): void {
                PlayersService.active?.togglePlaying();
            }
        }

        MediaControlButton {
            iconName: "skip_next"
            canUse: PlayersService.active?.canGoNext ?? false

            function onClicked(): void {
                PlayersService.active?.next();
            }
        }
    }

    component MediaControlButton: StyledRect {
        id: mediaControlButtonRoot

        required property string iconName
        required property bool canUse
        function onClicked(): void {
        }

        implicitWidth: Math.max(controlButtonIcon.implicitHeight, controlButtonIcon.implicitHeight) + Appearance.padding.small
        implicitHeight: implicitWidth

        StateLayer {
            disabled: !mediaControlButtonRoot.canUse
            radius: Appearance.rounding.full

            function onClicked(): void {
                mediaControlButtonRoot.onClicked();
            }
        }

        MaterialIcon {
            id: controlButtonIcon

            anchors.centerIn: parent
            anchors.verticalCenterOffset: font.pointSize * 0.05

            animate: true
            text: mediaControlButtonRoot.iconName
            color: mediaControlButtonRoot.canUse ? Colours.palette.m3onSurface : Colours.palette.m3outline
            font.pointSize: Appearance.font.size.large
        }
    }
}
