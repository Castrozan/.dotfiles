import Quickshell.Io
import QtQuick
import ".."
import "../.."

StatusIcon {
    id: vpnIcon

    property string serviceName: "openvpn-proton-paraguay.service"
    property bool isConnected: false

    iconText: "󰖂"
    iconColor: isConnected ? ThemeColors.accent : ThemeColors.foreground

    onClicked: {
        vpnToggleProcess.command = vpnIcon.isConnected ? ["vpn-off"] : ["vpn-py"];
        vpnToggleProcess.running = true;
    }

    Process {
        id: vpnStatusProcess
        command: ["systemctl", "is-active", vpnIcon.serviceName]
        running: false
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                vpnIcon.isConnected = data.trim() === "active";
            }
        }
    }

    Process {
        id: vpnToggleProcess
        command: ["vpn-py"]
        running: false
        onExited: vpnStatusProcess.running = true
    }

    Timer {
        interval: 5000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: vpnStatusProcess.running = true
    }
}
