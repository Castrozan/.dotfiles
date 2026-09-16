import Quickshell.Io
import QtQuick
import "../../dashboard/components"
import "../../dashboard"

UtilityToggleButton {
    id: wifiToggleButton

    iconName: "wifi"
    iconNameOff: "wifi_off"
    checked: wifiStatusIsPowered

    property bool wifiStatusIsPowered: false

    Process {
        id: wifiStatusQueryProcess
        command: ["nmcli", "radio", "wifi"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                wifiToggleButton.wifiStatusIsPowered = data.trim() === "enabled";
            }
        }
    }

    Process {
        id: wifiToggleEnableProcess
        command: ["nmcli", "radio", "wifi", "on"]
        onRunningChanged: {
            if (!running)
                wifiStatusPollTimer.restart();
        }
    }

    Process {
        id: wifiToggleDisableProcess
        command: ["nmcli", "radio", "wifi", "off"]
        onRunningChanged: {
            if (!running)
                wifiStatusPollTimer.restart();
        }
    }

    Timer {
        id: wifiStatusPollTimer
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: wifiStatusQueryProcess.running = true
    }

    onClicked: {
        if (wifiStatusIsPowered)
            wifiToggleDisableProcess.running = true;
        else
            wifiToggleEnableProcess.running = true;
    }
}
