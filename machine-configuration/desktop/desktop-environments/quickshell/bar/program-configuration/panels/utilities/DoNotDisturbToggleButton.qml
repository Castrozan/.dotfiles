import Quickshell.Io
import QtQuick
import "../../dashboard/components"
import "../../dashboard"

UtilityToggleButton {
    id: doNotDisturbToggleButton

    iconName: "do_not_disturb_off"
    iconNameOff: "do_not_disturb_on"
    checked: !doNotDisturbStatusIsEnabled

    property bool doNotDisturbStatusIsEnabled: false

    Process {
        id: doNotDisturbStatusQueryProcess
        command: ["makoctl", "mode"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                doNotDisturbToggleButton.doNotDisturbStatusIsEnabled = data.indexOf("do-not-disturb") !== -1;
            }
        }
    }

    Process {
        id: doNotDisturbModeToggleProcess
        command: ["makoctl", "mode", "-t", "do-not-disturb"]
        onRunningChanged: {
            if (!running)
                doNotDisturbStatusPollTimer.restart();
        }
    }

    Timer {
        id: doNotDisturbStatusPollTimer
        interval: 5000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: doNotDisturbStatusQueryProcess.running = true
    }

    onClicked: doNotDisturbModeToggleProcess.running = true
}
