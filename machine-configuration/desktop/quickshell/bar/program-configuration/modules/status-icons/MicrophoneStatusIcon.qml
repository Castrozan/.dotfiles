import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: microphoneIcon

    property bool isMuted: false

    iconText: isMuted ? "󰖁" : "󰍰"
    iconColor: isMuted ? ThemeColors.warning : ThemeColors.foreground

    onClicked: microphoneToggleProcess.running = true

    Process {
        id: microphoneStatusProcess
        command: ["hypr-microphone-toggle", "status"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    let parsed = JSON.parse(data);
                    microphoneIcon.isMuted = parsed.class === "muted";
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

    Component.onCompleted: microphoneStatusProcess.running = true
}
