import Quickshell.Services.Pipewire
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: outputDeviceTypeIcon

    readonly property PwNode defaultAudioSink: Pipewire.defaultAudioSink
    readonly property bool isMuted: defaultAudioSink?.audio?.muted ?? false
    readonly property string outputType: defaultAudioSink?.name.startsWith("bluez_") ? "bluetooth" : "speaker"

    iconText: {
        if (isMuted)
            return "󰖁";
        if (outputType === "bluetooth")
            return "󰋋";
        return "󰕾";
    }
    iconColor: isMuted ? ThemeColors.warning : ThemeColors.foreground

    onClicked: {
        const audio = defaultAudioSink?.audio;
        if (audio)
            audio.muted = !audio.muted;
    }

    PwObjectTracker {
        objects: [outputDeviceTypeIcon.defaultAudioSink]
    }
}
