import Quickshell.Io
import QtQuick
import "../../dashboard/components"
import "../../dashboard"

UtilityToggleButton {
    id: bluetoothToggleButton

    iconName: "bluetooth"
    iconNameOff: "bluetooth_disabled"
    checked: bluetoothStatusIsPowered

    property bool bluetoothStatusIsPowered: false

    Process {
        id: bluetoothStatusQueryProcess
        command: ["bluetoothctl", "show"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                bluetoothToggleButton.bluetoothStatusIsPowered = data.indexOf("Powered: yes") !== -1;
            }
        }
    }

    Process {
        id: bluetoothToggleOnProcess
        command: ["bluetoothctl", "power", "on"]
        onRunningChanged: {
            if (!running)
                bluetoothStatusPollTimer.restart();
        }
    }

    Process {
        id: bluetoothToggleOffProcess
        command: ["bluetoothctl", "power", "off"]
        onRunningChanged: {
            if (!running)
                bluetoothStatusPollTimer.restart();
        }
    }

    Timer {
        id: bluetoothStatusPollTimer
        interval: 5000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: bluetoothStatusQueryProcess.running = true
    }

    onClicked: {
        if (bluetoothStatusIsPowered)
            bluetoothToggleOffProcess.running = true;
        else
            bluetoothToggleOnProcess.running = true;
    }
}
