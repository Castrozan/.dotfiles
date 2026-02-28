import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: batteryPopoutRoot

    property bool active: false

    property int batteryCapacity: 0
    property string batteryStatus: "Unknown"
    property real batteryWattage: 0

    spacing: 12

    onActiveChanged: {
        if (active) {
            fetchBatteryCapacityProcess.running = true;
            fetchBatteryStatusProcess.running = true;
            fetchBatteryWattageProcess.running = true;
        }
    }

    Process {
        id: fetchBatteryCapacityProcess
        command: ["cat", "/sys/class/power_supply/BAT0/capacity"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                batteryPopoutRoot.batteryCapacity = parseInt(data.trim()) || 0;
            }
        }
    }

    Process {
        id: fetchBatteryStatusProcess
        command: ["cat", "/sys/class/power_supply/BAT0/status"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                batteryPopoutRoot.batteryStatus = data.trim();
            }
        }
    }

    Process {
        id: fetchBatteryWattageProcess
        command: ["cat", "/sys/class/power_supply/BAT0/power_now"]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                let microwatts = parseInt(data.trim()) || 0;
                batteryPopoutRoot.batteryWattage = microwatts / 1000000.0;
            }
        }
    }

    Text {
        text: "Battery"
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    RowLayout {
        spacing: 12

        Text {
            text: batteryPopoutRoot.batteryCapacity + "%"
            font.pixelSize: 28
            font.bold: true
            font.family: "JetBrainsMono Nerd Font"
            color: {
                if (batteryPopoutRoot.batteryCapacity <= 20 && batteryPopoutRoot.batteryStatus !== "Charging")
                    return ThemeColors.warning;
                return ThemeColors.foreground;
            }
        }

        ColumnLayout {
            spacing: 2

            Text {
                text: {
                    if (batteryPopoutRoot.batteryStatus === "Charging") return "⚡ Charging";
                    if (batteryPopoutRoot.batteryStatus === "Discharging") return "🔋 Discharging";
                    if (batteryPopoutRoot.batteryStatus === "Full") return "✓ Full";
                    return batteryPopoutRoot.batteryStatus;
                }
                font.pixelSize: 12
                font.family: "JetBrainsMono Nerd Font"
                color: ThemeColors.accent
            }

            Text {
                text: batteryPopoutRoot.batteryWattage > 0 ? batteryPopoutRoot.batteryWattage.toFixed(1) + "W" : ""
                font.pixelSize: 11
                font.family: "JetBrainsMono Nerd Font"
                color: ThemeColors.dim
                visible: batteryPopoutRoot.batteryWattage > 0
            }
        }
    }

    Rectangle {
        Layout.fillWidth: true
        height: 6
        radius: 3
        color: ThemeColors.surfaceTranslucent

        Rectangle {
            width: parent.width * (batteryPopoutRoot.batteryCapacity / 100.0)
            height: parent.height
            radius: 3
            color: {
                if (batteryPopoutRoot.batteryCapacity <= 20) return ThemeColors.warning;
                if (batteryPopoutRoot.batteryCapacity <= 10) return ThemeColors.error;
                return ThemeColors.accent;
            }

            Behavior on width {
                NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
            }
        }
    }
}
