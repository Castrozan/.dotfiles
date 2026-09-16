import Quickshell.Io
import QtQuick
import "../../dashboard/components"
import "../../dashboard"

UtilityToggleButton {
    id: nightLightToggleButton

    iconName: "nightlight"
    iconNameOff: "nightlight"
    checked: nightLightIsActive

    property bool nightLightIsActive: false

    Process {
        id: nightLightStatusQueryProcess
        command: ["bash", "-c", "pgrep hyprsunset > /dev/null && echo active || echo inactive"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                nightLightToggleButton.nightLightIsActive = data.trim() === "active";
            }
        }
    }

    Process {
        id: nightLightEnableProcess
        command: ["hyprsunset", "-t", "3500"]
    }

    Process {
        id: nightLightDisableProcess
        command: ["pkill", "hyprsunset"]
        onRunningChanged: {
            if (!running)
                nightLightStatusPollTimer.restart();
        }
    }

    Timer {
        id: nightLightStatusPollTimer
        interval: 5000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: nightLightStatusQueryProcess.running = true
    }

    onClicked: {
        if (nightLightIsActive)
            nightLightDisableProcess.running = true;
        else
            nightLightEnableProcess.running = true;
    }
}
