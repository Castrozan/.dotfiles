import Quickshell.Io
import Quickshell.Services.Pipewire
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: microphoneIcon

    readonly property PwNode defaultAudioSource: Pipewire.defaultAudioSource
    readonly property bool isMuted: defaultAudioSource?.audio?.muted ?? false

    iconText: isMuted ? "󰖁" : "󰍰"
    iconColor: isMuted ? ThemeColors.warning : ThemeColors.foreground

    onClicked: microphoneToggleProcess.running = true

    PwObjectTracker {
        objects: [microphoneIcon.defaultAudioSource]
    }

    Process {
        id: microphoneToggleProcess
        command: ["hypr-microphone-toggle", "toggle"]
        running: false
    }
}
