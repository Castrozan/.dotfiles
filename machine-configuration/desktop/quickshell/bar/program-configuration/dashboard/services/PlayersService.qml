pragma Singleton

import Quickshell
import Quickshell.Services.Mpris

Singleton {
    id: playersServiceRoot

    readonly property list<MprisPlayer> list: Mpris.players.values

    readonly property MprisPlayer bestAutoPlayer: {
        let pausedPlayer = null;
        for (const player of list) {
            if (player.playbackState === MprisPlaybackState.Playing)
                return player;
            if (!pausedPlayer && player.playbackState === MprisPlaybackState.Paused)
                pausedPlayer = player;
        }
        return pausedPlayer ?? list[0] ?? null;
    }

    readonly property MprisPlayer active: manualActive ?? bestAutoPlayer
    property MprisPlayer manualActive

    function getIdentity(player: MprisPlayer): string {
        return player.identity;
    }
}
