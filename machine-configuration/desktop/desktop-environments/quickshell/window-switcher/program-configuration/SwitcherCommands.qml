pragma ComponentBehavior: Bound

import Quickshell
import Quickshell.Io

Scope {
    id: switcherCommands

    signal openRequested
    signal nextRequested
    signal previousRequested
    signal confirmRequested
    signal cancelRequested

    IpcHandler {
        target: "switcher"

        function open(): void {
            switcherCommands.openRequested();
        }

        function next(): void {
            switcherCommands.nextRequested();
        }

        function prev(): void {
            switcherCommands.previousRequested();
        }

        function confirm(): void {
            switcherCommands.confirmRequested();
        }

        function cancel(): void {
            switcherCommands.cancelRequested();
        }
    }

    SocketServer {
        active: true
        path: Quickshell.env("XDG_RUNTIME_DIR") + "/quickshell-switcher.sock"

        handler: Socket {
            parser: SplitParser {
                splitMarker: "\n"
                onRead: message => {
                    let command = message.trim();
                    if (command === "open")
                        switcherCommands.openRequested();
                    else if (command === "next")
                        switcherCommands.nextRequested();
                    else if (command === "prev")
                        switcherCommands.previousRequested();
                    else if (command === "confirm")
                        switcherCommands.confirmRequested();
                    else if (command === "cancel")
                        switcherCommands.cancelRequested();
                }
            }
        }
    }
}
