import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: keyboardBacklightIcon
    visible: MachineFeatures.hasKeyboardBacklight

    property int brightnessLevel: 2
    readonly property var levels: [0, 5, 25, 50, 100]
    readonly property var levelIcons: ["󰌐", "󰌌", "󰌌", "󰌌", "󰌌"]
    readonly property var levelOpacities: [0.3, 0.4, 0.6, 0.8, 1.0]

    iconText: levelIcons[brightnessLevel]
    iconColor: ThemeColors.foreground
    opacity: levelOpacities[brightnessLevel]

    onClicked: {
        brightnessLevel = (brightnessLevel + 1) % levels.length;
        kbdBacklightProcess.command = ["set-keyboard-backlight-brightness", String(levels[brightnessLevel])];
        kbdBacklightProcess.running = true;
    }

    Behavior on opacity {
        NumberAnimation { duration: 150 }
    }

    Process {
        id: kbdBacklightProcess
        command: ["set-keyboard-backlight-brightness", "5"]
        running: false
    }
}
