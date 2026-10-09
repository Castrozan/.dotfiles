pragma Singleton

import Quickshell
import Quickshell.Hyprland
import QtQuick

Singleton {
    id: hyprlandEventsServiceRoot

    signal fullscreenChanged
    signal windowLayoutChanged
    signal activeWindowChanged

    Connections {
        target: Hyprland

        function onRawEvent(event) {
            if (event.name === "fullscreen")
                hyprlandEventsServiceRoot.fullscreenChanged();
            else if (["openwindow", "closewindow", "movewindow", "movewindowv2"].includes(event.name))
                hyprlandEventsServiceRoot.windowLayoutChanged();
            else if (event.name === "activewindow" || event.name === "activewindowv2")
                hyprlandEventsServiceRoot.activeWindowChanged();
        }
    }
}
