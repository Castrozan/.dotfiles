import Quickshell
import Quickshell.Io
import QtQuick
import "drawers"

Scope {
    id: drawersRoot

    signal osdSocketMessageReceived(string message)
    signal hyprlandFullscreenEventReceived

    Connections {
        target: HyprlandEventsService
        function onFullscreenChanged() {
            drawersRoot.hyprlandFullscreenEventReceived();
        }
    }

    SocketServer {
        active: true
        path: Quickshell.env("XDG_RUNTIME_DIR") + "/quickshell-osd.sock"

        handler: Socket {
            parser: SplitParser {
                splitMarker: "\n"
                onRead: message => drawersRoot.osdSocketMessageReceived(message)
            }
        }
    }

    Variants {
        model: Quickshell.screens

        ScreenDrawers {
            required property var modelData
            screen: modelData
            shellEvents: drawersRoot
        }
    }
}
