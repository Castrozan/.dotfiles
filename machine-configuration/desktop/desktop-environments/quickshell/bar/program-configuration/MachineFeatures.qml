pragma Singleton

import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: machineFeaturesRoot

    property string hostname: ""
    property string batteryPath: ""

    readonly property bool hasKeyboardBacklight: hostname === "nixos"
    readonly property bool hasBattery: batteryPath !== ""

    FileView {
        id: hostnameFileView
        path: "/etc/hostname"
        blockLoading: true
        onLoaded: machineFeaturesRoot.hostname = text().trim()
    }

    Process {
        id: batteryDetectProcess
        command: ["bash", "-c", "for d in /sys/class/power_supply/BAT*; do [ -f \"$d/capacity\" ] && echo \"$d\" && exit; done"]
        running: true
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                machineFeaturesRoot.batteryPath = data.trim();
            }
        }
    }
}
