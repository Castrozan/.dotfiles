pragma Singleton

import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: hyprlandEventsServiceRoot

    signal fullscreenChanged()
    signal windowLayoutChanged()
    signal activeWindowChanged()

    readonly property string hyprlandSocket2Path: Quickshell.env("XDG_RUNTIME_DIR") + "/hypr/" + Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE") + "/.socket2.sock"

    Process {
        id: hyprlandEventMonitorProcess

        command: ["nc", "-U", hyprlandEventsServiceRoot.hyprlandSocket2Path]
        running: true

        stdout: SplitParser {
            splitMarker: "\n"
            onRead: data => {
                if (data.startsWith("fullscreen>>"))
                    hyprlandEventsServiceRoot.fullscreenChanged();
                else if (data.startsWith("openwindow>>") || data.startsWith("closewindow>>") || data.startsWith("movewindow>>"))
                    hyprlandEventsServiceRoot.windowLayoutChanged();
                else if (data.startsWith("activewindow>>"))
                    hyprlandEventsServiceRoot.activeWindowChanged();
            }
        }

        onExited: running = true
    }
}
