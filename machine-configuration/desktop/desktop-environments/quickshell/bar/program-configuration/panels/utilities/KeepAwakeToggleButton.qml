import Quickshell.Io
import QtQuick
import "../../dashboard/components"
import "../../dashboard"

UtilityToggleButton {
    id: keepAwakeToggleButton

    iconName: "coffee"
    iconNameOff: "coffee"
    checked: keepAwakeIsActive

    property bool keepAwakeIsActive: false

    Process {
        id: keepAwakeStatusQueryProcess
        command: ["bash", "-c", "pgrep -f 'systemd-inhibit.*idle' > /dev/null && echo active || echo inactive"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                keepAwakeToggleButton.keepAwakeIsActive = data.trim() === "active";
            }
        }
    }

    Process {
        id: keepAwakeEnableProcess
        command: ["systemd-inhibit", "--what=idle", "--who=quickshell", "--why=Keep Awake", "--mode=block", "sleep", "infinity"]
    }

    Process {
        id: keepAwakeDisableProcess
        command: ["bash", "-c", "pkill -f 'systemd-inhibit.*idle'"]
        onRunningChanged: {
            if (!running)
                keepAwakeStatusPollTimer.restart();
        }
    }

    Timer {
        id: keepAwakeStatusPollTimer
        interval: 5000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: keepAwakeStatusQueryProcess.running = true
    }

    onClicked: {
        if (keepAwakeIsActive)
            keepAwakeDisableProcess.running = true;
        else
            keepAwakeEnableProcess.running = true;
    }
}
