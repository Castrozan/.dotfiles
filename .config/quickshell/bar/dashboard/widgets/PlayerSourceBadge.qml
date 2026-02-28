pragma ComponentBehavior: Bound

import "../components"
import "../services"
import ".."
import Quickshell.Services.Mpris
import QtQuick

StyledRect {
    id: playerSourceBadgeRoot

    implicitWidth: badgeRow.implicitWidth + Appearance.padding.normal * 2
    implicitHeight: badgeRow.implicitHeight + Appearance.padding.small * 2

    radius: Appearance.rounding.full
    color: Colours.palette.m3surfaceContainer

    Row {
        id: badgeRow

        anchors.centerIn: parent
        spacing: Appearance.spacing.small

        MaterialIcon {
            anchors.verticalCenter: parent.verticalCenter
            text: "music_note"
            color: Colours.palette.m3primary
            font.pointSize: Appearance.font.size.small
        }

        StyledText {
            anchors.verticalCenter: parent.verticalCenter
            text: PlayersService.active ? PlayersService.getIdentity(PlayersService.active) : "No player"
            font.pointSize: Appearance.font.size.small
            color: Colours.palette.m3onSurface
        }
    }

    StateLayer {
        function onClicked(): void {
            const currentIndex = PlayersService.list.indexOf(PlayersService.active);
            const nextIndex = (currentIndex + 1) % PlayersService.list.length;
            if (PlayersService.list.length > 1)
                PlayersService.manualActive = PlayersService.list[nextIndex];
        }
    }
}
