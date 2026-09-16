import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: outputDeviceTypeIcon

    property bool isMuted: false
    property string outputType: "speaker"

    iconText: {
        if (isMuted) return "󰖁";
        if (outputType === "bluetooth") return "󰋋";
        return "󰕾";
    }
    iconColor: isMuted ? ThemeColors.warning : ThemeColors.foreground

    onClicked: outputMuteToggleProcess.running = true

    Process {
        id: outputDefaultSinkProcess
        command: ["pactl", "get-default-sink"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const sinkName = data.trim();
                outputDeviceTypeIcon.outputType = sinkName.startsWith("bluez_") ? "bluetooth" : "speaker";
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
                outputDeviceTypeIcon.isMuted = data.trim() === "Mute: yes";
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

    Timer {
        interval: 15000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            outputDefaultSinkProcess.running = true;
            outputMuteStatusProcess.running = true;
        }
    }
}
