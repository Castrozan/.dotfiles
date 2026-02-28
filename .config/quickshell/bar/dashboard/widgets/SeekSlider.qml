pragma ComponentBehavior: Bound

import "../components"
import "../services"
import ".."
import QtQuick

StyledSlider {
    id: seekSliderRoot

    property bool seeking: false

    from: 0
    to: PlayersService.active?.length ?? 0
    value: seeking ? value : (PlayersService.active?.position ?? 0)

    implicitHeight: 24

    onPressedChanged: {
        if (pressed)
            seeking = true;
        else {
            if (PlayersService.active)
                PlayersService.active.position = value;
            seeking = false;
        }
    }
}
