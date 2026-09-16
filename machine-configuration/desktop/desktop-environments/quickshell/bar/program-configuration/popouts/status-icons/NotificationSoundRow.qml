import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIconsPopoutRow {
    id: notificationSoundRowRoot

    required property bool active

    property bool notificationSoundMuted: false

    onActiveChanged: {
        if (active) {
            notificationSoundStatusProcess.running = true;
        }
    }

    Process {
        id: notificationSoundStatusProcess
        command: ["hypr-notification-sound-toggle", "status"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    let parsed = JSON.parse(data);
                    notificationSoundRowRoot.notificationSoundMuted = parsed.class === "muted";
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

    rowIconText: notificationSoundRowRoot.notificationSoundMuted ? "󰂛" : "󰂚"
    rowIconColor: notificationSoundRowRoot.notificationSoundMuted ? ThemeColors.warning : ThemeColors.foreground
    rowLabel: "Notifications"
    rowStateText: notificationSoundRowRoot.notificationSoundMuted ? "muted" : ""
    onRowClicked: notificationSoundToggleProcess.running = true
}
