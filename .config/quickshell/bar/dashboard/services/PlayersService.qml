pragma Singleton

import Quickshell
import Quickshell.Services.Mpris

Singleton {
    id: playersServiceRoot

    readonly property list<MprisPlayer> list: Mpris.players.values

    readonly property MprisPlayer activePlayingPlayer: {
        for (const player of list) {
            if (player.playbackState === MprisPlaybackState.Playing)
                return player;
        }
        return null;
    }

    readonly property MprisPlayer active: manualActive ?? activePlayingPlayer ?? list[0] ?? null
    property MprisPlayer manualActive

    function getIdentity(player: MprisPlayer): string {
        return player.identity;
    }
}
