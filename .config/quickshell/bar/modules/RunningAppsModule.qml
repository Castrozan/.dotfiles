import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Qt5Compat.GraphicalEffects
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: runningAppsModuleRoot

    spacing: 2

    property var runningAppsByClass: []
    property string focusedWindowClass: ""
    property var firstSeenOrderByClass: ({})
    property int firstSeenOrderNextIndex: 0

    readonly property var windowClassToIconName: ({
        "chrome-global": "google-chrome",
        "code": "vscode",
        "code - insiders": "vscode-insiders",
        "cursor": "cursor",
    })

    function _resolveIconName(windowClass: string): string {
        let lowerClass = windowClass.toLowerCase();
        return windowClassToIconName[lowerClass] ?? lowerClass;
    }

    readonly property string hyprlandSocket2Path: Quickshell.env("XDG_RUNTIME_DIR") + "/hypr/" + Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE") + "/.socket2.sock"

    Component.onCompleted: _fetchRunningClients()

    function _fetchRunningClients(): void {
        if (fetchRunningClientsProcess.running)
            fetchRunningClientsProcess.running = false;
        fetchRunningClientsProcess.running = true;
    }

    function _parseClientsAndRebuildAppList(clientsJson: string): void {
        let clients;
        try {
            clients = JSON.parse(clientsJson);
        } catch (error) {
            return;
        }

        let mostRecentWindowByClass = {};
        let detectedFocusedClass = "";

        for (let i = 0; i < clients.length; i++) {
            let client = clients[i];
            let windowClass = client.class || "";
            if (windowClass === "")
                continue;

            if (client.focusHistoryID === 0)
                detectedFocusedClass = windowClass;

            let existing = mostRecentWindowByClass[windowClass];
            if (!existing || (client.focusHistoryID < existing.focusHistoryID)) {
                mostRecentWindowByClass[windowClass] = {
                    windowClass: windowClass,
                    address: client.address,
                    focusHistoryID: client.focusHistoryID ?? 9999
                };
            }
        }

        let updatedFirstSeenOrder = firstSeenOrderByClass;
        let updatedNextIndex = firstSeenOrderNextIndex;

        for (let cls in mostRecentWindowByClass) {
            if (updatedFirstSeenOrder[cls] === undefined) {
                updatedFirstSeenOrder[cls] = updatedNextIndex;
                updatedNextIndex++;
            }
        }

        for (let cls in updatedFirstSeenOrder) {
            if (!mostRecentWindowByClass[cls])
                delete updatedFirstSeenOrder[cls];
        }

        firstSeenOrderByClass = updatedFirstSeenOrder;
        firstSeenOrderNextIndex = updatedNextIndex;

        let sortedAppList = [];
        for (let cls in mostRecentWindowByClass)
            sortedAppList.push(mostRecentWindowByClass[cls]);

        sortedAppList.sort((a, b) => firstSeenOrderByClass[a.windowClass] - firstSeenOrderByClass[b.windowClass]);

        runningAppsByClass = sortedAppList;
        focusedWindowClass = detectedFocusedClass;
    }

    Process {
        id: fetchRunningClientsProcess
        command: ["hyprctl", "clients", "-j"]
        running: false

        stdout: SplitParser {
            splitMarker: ""
            onRead: data => runningAppsModuleRoot._parseClientsAndRebuildAppList(data)
        }
    }

    Process {
        id: hyprlandSocket2EventMonitorProcess
        command: ["nc", "-U", hyprlandSocket2Path]
        running: true

        stdout: SplitParser {
            splitMarker: "\n"
            onRead: data => {
                if (data.startsWith("openwindow>>") || data.startsWith("closewindow>>") || data.startsWith("movewindow>>") || data.startsWith("activewindow>>")) {
                    runningAppsRefreshDebounceTimer.restart();
                }
            }
        }

        onExited: running = true
    }

    Timer {
        id: runningAppsRefreshDebounceTimer
        interval: 100
        onTriggered: runningAppsModuleRoot._fetchRunningClients()
    }

    Repeater {
        model: runningAppsModuleRoot.runningAppsByClass

        Rectangle {
            id: runningAppDelegate

            required property var modelData
            required property int index

            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 28
            Layout.preferredHeight: 28

            radius: 6
            color: runningAppMouseArea.containsMouse ? ThemeColors.surfaceTranslucent : "transparent"

            Image {
                id: runningAppIcon
                anchors.centerIn: parent
                width: 16
                height: 16
                source: Quickshell.iconPath(runningAppsModuleRoot._resolveIconName(runningAppDelegate.modelData.windowClass), true)
                sourceSize: Qt.size(16, 16)
                smooth: true
                visible: status === Image.Ready
            }

            Colorize {
                anchors.fill: runningAppIcon
                source: runningAppIcon
                visible: runningAppIcon.visible
                hue: ThemeColors.foreground.hslHue
                saturation: ThemeColors.foreground.hslSaturation
                lightness: 0.3
            }

            Text {
                anchors.centerIn: parent
                visible: runningAppIcon.status !== Image.Ready
                text: runningAppDelegate.modelData.windowClass.charAt(0).toUpperCase()
                font.pixelSize: 14
                font.bold: true
                font.family: "JetBrainsMono Nerd Font"
                color: ThemeColors.foreground
            }

            Rectangle {
                id: focusedAppAccentIndicator
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: -2
                width: 3
                height: runningAppDelegate.modelData.windowClass === runningAppsModuleRoot.focusedWindowClass ? 12 : 4
                radius: 1.5
                color: ThemeColors.accent

                Behavior on height {
                    NumberAnimation {
                        duration: 150
                        easing.type: Easing.OutQuad
                    }
                }
            }

            MouseArea {
                id: runningAppMouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor

                onClicked: {
                    Hyprland.dispatch(`focuswindow address:${runningAppDelegate.modelData.address}`);
                }
            }
        }
    }
}
