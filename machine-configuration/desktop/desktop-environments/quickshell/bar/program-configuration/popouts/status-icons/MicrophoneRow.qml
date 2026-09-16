import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIconsPopoutRow {
    id: microphoneRowRoot

    required property bool active

    property bool microphoneMuted: false

    onActiveChanged: {
        if (active) {
            microphoneStatusProcess.running = true;
        }
    }

    Process {
        id: microphoneStatusProcess
        command: ["hypr-microphone-toggle", "status"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    let parsed = JSON.parse(data);
                    microphoneRowRoot.microphoneMuted = parsed.class === "muted";
                } catch (e) {}
            }
        }
    }

    Process {
        id: microphoneToggleProcess
        command: ["hypr-microphone-toggle", "toggle"]
        running: false
        onExited: microphoneStatusProcess.running = true
    }

    rowIconText: microphoneRowRoot.microphoneMuted ? "󰖁" : "󰍰"
    rowIconColor: microphoneRowRoot.microphoneMuted ? ThemeColors.warning : ThemeColors.foreground
    rowLabel: "Microphone"
    rowStateText: microphoneRowRoot.microphoneMuted ? "muted" : ""
    onRowClicked: microphoneToggleProcess.running = true
}
