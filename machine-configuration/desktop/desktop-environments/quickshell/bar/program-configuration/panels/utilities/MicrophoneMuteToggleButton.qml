import Quickshell.Io
import QtQuick
import "../../dashboard/components"
import "../../dashboard"

UtilityToggleButton {
    id: microphoneMuteToggleButton

    iconName: "mic"
    iconNameOff: "mic_off"
    checked: !microphoneStatusIsMuted

    property bool microphoneStatusIsMuted: false

    Process {
        id: microphoneStatusQueryProcess
        command: ["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                microphoneMuteToggleButton.microphoneStatusIsMuted = data.indexOf("[MUTED]") !== -1;
            }
        }
    }

    Process {
        id: microphoneMuteToggleProcess
        command: ["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"]
        onRunningChanged: {
            if (!running)
                microphoneStatusPollTimer.restart();
        }
    }

    Timer {
        id: microphoneStatusPollTimer
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: microphoneStatusQueryProcess.running = true
    }

    onClicked: microphoneMuteToggleProcess.running = true
}
