pragma Singleton

import Quickshell
import Quickshell.Services.Mpris

Singleton {
    id: playersServiceRoot

    readonly property list<MprisPlayer> list: Mpris.players.values
    readonly property MprisPlayer active: manualActive ?? list[0] ?? null
    property MprisPlayer manualActive

    function getIdentity(player: MprisPlayer): string {
        return player.identity;
    }
}
