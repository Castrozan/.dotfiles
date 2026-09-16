import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIconsPopoutRow {
    id: outputSoundRowRoot

    required property bool active

    property bool outputMuted: false
    property string outputDeviceType: "speaker"

    onActiveChanged: {
        if (active) {
            outputDefaultSinkProcess.running = true;
            outputMuteStatusProcess.running = true;
        }
    }

    Process {
        id: outputDefaultSinkProcess
        command: ["pactl", "get-default-sink"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const sinkName = data.trim();
                outputSoundRowRoot.outputDeviceType = sinkName.startsWith("bluez_") ? "bluetooth" : "speaker";
            }
        }
    }

    Process {
        id: outputMuteStatusProcess
        command: ["bash", "-c", "pactl get-default-sink | xargs pactl get-sink-mute"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                outputSoundRowRoot.outputMuted = data.trim() === "Mute: yes";
            }
        }
    }

    Process {
        id: outputMuteToggleProcess
        command: ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"]
        running: false
        onExited: {
            outputDefaultSinkProcess.running = true;
            outputMuteStatusProcess.running = true;
        }
    }

    rowIconText: {
        if (outputSoundRowRoot.outputMuted)
            return "󰖁";
        if (outputSoundRowRoot.outputDeviceType === "bluetooth")
            return "󰋋";
        return "󰕾";
    }
    rowIconColor: outputSoundRowRoot.outputMuted ? ThemeColors.warning : ThemeColors.foreground
    rowLabel: "Sound"
    rowStateText: outputSoundRowRoot.outputMuted ? "muted" : ""
    onRowClicked: outputMuteToggleProcess.running = true
}
