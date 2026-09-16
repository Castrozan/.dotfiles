import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import QtQuick
import ".."
import "running-applications"

Item {
    id: runningAppsModuleRoot

    property var runningAppsByClass: []
    property string focusedWindowClass: ""
    property var firstSeenOrderByClass: ({})
    property int firstSeenOrderNextIndex: 0

    readonly property int iconCellSize: 28
    readonly property int iconCellSpacing: 2
    readonly property int iconCellStride: iconCellSize + iconCellSpacing
    readonly property int totalRunningAppsCount: runningAppsByClass.length
    readonly property int maxAppsFittingByHeight: height < iconCellSize ? 0 : Math.floor((height + iconCellSpacing) / iconCellStride)
    readonly property bool hasMoreAppsThanFit: totalRunningAppsCount > maxAppsFittingByHeight
    readonly property int visibleAppsCount: hasMoreAppsThanFit ? Math.max(0, maxAppsFittingByHeight - 1) : totalRunningAppsCount
    readonly property var visibleApps: runningAppsByClass.slice(0, visibleAppsCount)
    readonly property int hiddenAppsCount: totalRunningAppsCount - visibleAppsCount

    readonly property var windowClassToIconName: ({
            "chrome-global": "google-chrome",
            "code": "vscode",
            "code - insiders": "vscode-insiders",
            "cursor": "cursor"
        })

    function _resolveIconName(windowClass: string): string {
        let lowerClass = windowClass.toLowerCase();
        return windowClassToIconName[lowerClass] ?? lowerClass;
    }

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

        let updatedFirstSeenOrder = Object.assign({}, firstSeenOrderByClass);
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

    Connections {
        target: HyprlandEventsService
        function onWindowLayoutChanged() {
            runningAppsRefreshDebounceTimer.restart();
        }
        function onActiveWindowChanged() {
            runningAppsRefreshDebounceTimer.restart();
        }
    }

    Timer {
        id: runningAppsRefreshDebounceTimer
        interval: 100
        onTriggered: runningAppsModuleRoot._fetchRunningClients()
    }

    Column {
        id: visibleAppsColumn
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: runningAppsModuleRoot.iconCellSpacing

        Repeater {
            model: runningAppsModuleRoot.visibleApps

            RunningApplicationIcon {
                required property var modelData

                application: modelData
                cellSize: runningAppsModuleRoot.iconCellSize
                iconName: runningAppsModuleRoot._resolveIconName(modelData.windowClass)
                focused: modelData.windowClass === runningAppsModuleRoot.focusedWindowClass
                onActivated: Hyprland.dispatch(`focuswindow address:${modelData.address}`)
            }
        }

        Rectangle {
            id: hiddenAppsOverflowIndicator

            visible: runningAppsModuleRoot.hasMoreAppsThanFit
            width: runningAppsModuleRoot.iconCellSize
            height: runningAppsModuleRoot.iconCellSize
            radius: 6
            color: hiddenAppsOverflowMouseArea.containsMouse ? ThemeColors.surfaceTranslucent : "transparent"

            Text {
                anchors.centerIn: parent
                text: "+" + runningAppsModuleRoot.hiddenAppsCount
                color: ThemeColors.dim
                font.pixelSize: 11
                font.bold: true
                font.family: "JetBrainsMono Nerd Font"
            }

            MouseArea {
                id: hiddenAppsOverflowMouseArea
                anchors.fill: parent
                hoverEnabled: true
            }
        }
    }
}
