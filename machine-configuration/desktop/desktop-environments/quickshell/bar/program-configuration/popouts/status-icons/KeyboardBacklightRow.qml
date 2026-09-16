import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIconsPopoutRow {
    id: keyboardBacklightRowRoot

    required property bool active

    property int keyboardBacklightLevel: 2
    readonly property var keyboardBacklightLevels: [0, 5, 25, 50, 100]
    readonly property var keyboardBacklightIcons: ["󰌐", "󰌌", "󰌌", "󰌌", "󰌌"]
    readonly property var keyboardBacklightOpacities: [0.3, 0.4, 0.6, 0.8, 1.0]

    Process {
        id: keyboardBacklightSetProcess
        command: ["set-keyboard-backlight-brightness", "5"]
        running: false
    }

    visible: MachineFeatures.hasKeyboardBacklight
    rowIconText: keyboardBacklightRowRoot.keyboardBacklightIcons[keyboardBacklightRowRoot.keyboardBacklightLevel]
    rowIconColor: ThemeColors.foreground
    rowIconOpacity: keyboardBacklightRowRoot.keyboardBacklightOpacities[keyboardBacklightRowRoot.keyboardBacklightLevel]
    rowLabel: "Keyboard light"
    rowStateText: keyboardBacklightRowRoot.keyboardBacklightLevels[keyboardBacklightRowRoot.keyboardBacklightLevel] + "%"
    onRowClicked: {
        keyboardBacklightRowRoot.keyboardBacklightLevel = (keyboardBacklightRowRoot.keyboardBacklightLevel + 1) % keyboardBacklightRowRoot.keyboardBacklightLevels.length;
        keyboardBacklightSetProcess.command = ["set-keyboard-backlight-brightness", String(keyboardBacklightRowRoot.keyboardBacklightLevels[keyboardBacklightRowRoot.keyboardBacklightLevel])];
        keyboardBacklightSetProcess.running = true;
    }
}
