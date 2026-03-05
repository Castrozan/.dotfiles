pragma ComponentBehavior: Bound

import Quickshell.Io
import "../dashboard/components"
import "../dashboard"
import QtQuick
import QtQuick.Layouts

Item {
    id: utilitiesContentRoot

    implicitWidth: utilitiesToggleGrid.implicitWidth + Appearance.padding.large * 2
    implicitHeight: utilitiesToggleGrid.implicitHeight + Appearance.padding.large * 2

    GridLayout {
        id: utilitiesToggleGrid

        anchors.centerIn: parent
        columns: 3
        rowSpacing: Appearance.spacing.small
        columnSpacing: Appearance.spacing.small

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

        UtilityToggleButton {
            id: nightLightToggleButton

            iconName: "nightlight"
            iconNameOff: "nightlight"
            checked: nightLightIsActive

            property bool nightLightIsActive: false

            Process {
                id: nightLightStatusQueryProcess
                command: ["bash", "-c", "hyprctl -j getoption decoration:screen_shader | grep -q '\"str\": \"\"' && echo inactive || echo active"]
                stdout: SplitParser {
                    splitMarker: ""
                    onRead: data => {
                        nightLightToggleButton.nightLightIsActive = data.trim() === "active";
                    }
                }
            }

            Process {
                id: nightLightEnableProcess
                command: ["hyprctl", "keyword", "decoration:screen_shader", "~/.config/hypr/shaders/nightlight.glsl"]
                onRunningChanged: {
                    if (!running)
                        nightLightStatusPollTimer.restart();
                }
            }

            Process {
                id: nightLightDisableProcess
                command: ["hyprctl", "keyword", "decoration:screen_shader", ""]
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

    }

    component UtilityToggleButton: IconButton {
        property string iconName
        property string iconNameOff: iconName

        Layout.alignment: Qt.AlignHCenter

        icon: checked ? iconName : iconNameOff
        type: IconButton.Tonal
        toggle: true

        implicitWidth: 48
        implicitHeight: 48

        font.pointSize: Appearance.font.size.extraLarge
    }
}
