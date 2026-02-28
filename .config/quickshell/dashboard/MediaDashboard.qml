import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Services.Mpris
import QtQuick

Scope {
    id: mediaDashboardRoot

    property bool dashboardVisible: false

    readonly property MprisPlayer activePlayer: {
        let players = Mpris.players;
        let firstAvailable = null;
        for (let i = 0; i < players.count; i++) {
            let player = players.get(i);
            if (player.playbackState === MprisPlaybackState.Playing)
                return player;
            if (!firstAvailable)
                firstAvailable = player;
        }
        return firstAvailable;
    }

    function toggleDashboard(): void {
        dashboardVisible = !dashboardVisible;
    }

    IpcHandler {
        target: "dashboard"

        function toggle(): void {
            mediaDashboardRoot.toggleDashboard();
        }
    }

    PanelWindow {
        id: dashboardPanel

        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }

        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "quickshell-dashboard"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

        color: "transparent"
        surfaceFormat.opaque: false

        visible: mediaDashboardRoot.dashboardVisible

        Rectangle {
            anchors.fill: parent
            color: Qt.rgba(0, 0, 0, 0.35)

            MouseArea {
                anchors.fill: parent
                onClicked: mediaDashboardRoot.dashboardVisible = false
            }
        }

        MediaDashboardPanel {
            id: dashboardPanelContent
            anchors.horizontalCenter: parent.horizontalCenter
            y: 80
            activePlayer: mediaDashboardRoot.activePlayer

            MouseArea {
                anchors.fill: parent
                onClicked: function(mouse) { mouse.accepted = true; }
            }
        }
    }
}
