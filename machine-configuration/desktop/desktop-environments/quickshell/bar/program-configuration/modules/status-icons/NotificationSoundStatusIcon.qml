import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: notificationSoundIcon

    property bool isMuted: false

    iconText: isMuted ? "󰂛" : "󰂚"
    iconColor: isMuted ? ThemeColors.warning : ThemeColors.foreground

    onClicked: notificationSoundToggleProcess.running = true

    Process {
        id: notificationSoundStatusProcess
        command: ["hypr-notification-sound-toggle", "status"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    let parsed = JSON.parse(data);
                    notificationSoundIcon.isMuted = parsed.class === "muted";
                } catch (e) {}
            }
        }
    }

    Process {
        id: notificationSoundToggleProcess
        command: ["hypr-notification-sound-toggle", "toggle"]
        running: false
        onExited: notificationSoundStatusProcess.running = true
    }

    Component.onCompleted: notificationSoundStatusProcess.running = true
}
