pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Hyprland
import "../common"

/**
 * Provides access to some Hyprland data not available in Quickshell.Hyprland.
 */
Singleton {
    id: root
    readonly property bool active: GlobalStates.overviewOpen
    property bool initialized: false
    property var windowList: []
    property var addresses: []
    property var windowByAddress: ({})
    property var workspaces: []
    property var allWorkspaces: []
    property var workspaceIds: []
    property var workspaceById: ({})
    property var activeWorkspace: null
    property var monitors: []
    property var layers: ({})
    property bool pendingWindowsUpdate: false
    property bool pendingMonitorsUpdate: false
    property bool pendingLayersUpdate: false
    property bool pendingWorkspacesUpdate: false
    property bool pendingActiveWorkspaceUpdate: false

    function updateAll() {
        scheduleUpdates(true, true, true, true, true);
    }

    function refreshAll() {
        updateAll();
        flushPendingUpdates();
    }

    function scheduleUpdates(windows, monitors, layers, workspaces, activeWorkspace) {
        if (!active)
            return;
        pendingWindowsUpdate = pendingWindowsUpdate || !!windows;
        pendingMonitorsUpdate = pendingMonitorsUpdate || !!monitors;
        pendingLayersUpdate = pendingLayersUpdate || !!layers;
        pendingWorkspacesUpdate = pendingWorkspacesUpdate || !!workspaces;
        pendingActiveWorkspaceUpdate = pendingActiveWorkspaceUpdate || !!activeWorkspace;

        const debounceMs = Math.max(0, Config.options.hacks.hyprlandEventDebounceMs);
        if (debounceMs === 0) {
            flushPendingUpdates();
        } else {
            eventDebounceTimer.interval = debounceMs;
            eventDebounceTimer.restart();
        }
    }

    function flushPendingUpdates() {
        if (!active)
            return;
        queries.refresh(pendingWindowsUpdate, pendingMonitorsUpdate, pendingLayersUpdate, pendingWorkspacesUpdate, pendingActiveWorkspaceUpdate);
        pendingWindowsUpdate = false;
        pendingMonitorsUpdate = false;
        pendingLayersUpdate = false;
        pendingWorkspacesUpdate = false;
        pendingActiveWorkspaceUpdate = false;
    }

    function biggestWindowForWorkspace(workspaceId) {
        const windowsInThisWorkspace = HyprlandData.windowList.filter(w => w.workspace.id == workspaceId);
        return windowsInThisWorkspace.reduce((maxWin, win) => {
            const maxArea = (maxWin?.size?.[0] ?? 0) * (maxWin?.size?.[1] ?? 0);
            const winArea = (win?.size?.[0] ?? 0) * (win?.size?.[1] ?? 0);
            return winArea > maxArea ? win : maxWin;
        }, null);
    }

    onActiveChanged: {
        if (!initialized)
            return;
        if (active) {
            Qt.callLater(root.refreshAll);
            return;
        }
        eventDebounceTimer.stop();
        pendingWindowsUpdate = false;
        pendingMonitorsUpdate = false;
        pendingLayersUpdate = false;
        pendingWorkspacesUpdate = false;
        pendingActiveWorkspaceUpdate = false;
    }

    Component.onCompleted: {
        initialized = true;
        if (active)
            Qt.callLater(root.refreshAll);
    }

    HyprlandEventUpdates {
        enabled: root.active
        onUpdatesRequested: (windows, monitors, layers, workspaces, activeWorkspace) => root.scheduleUpdates(windows, monitors, layers, workspaces, activeWorkspace)
    }

    Timer {
        id: eventDebounceTimer
        interval: Math.max(0, Config.options.hacks.hyprlandEventDebounceMs)
        repeat: false
        onTriggered: root.flushPendingUpdates()
    }

    HyprlandQueryProcesses {
        id: queries
        active: root.active

        onWindowsReceived: windows => {
            root.windowList = windows;
            let windowByAddress = {};
            for (const window of windows)
                windowByAddress[window.address] = window;
            root.windowByAddress = windowByAddress;
            root.addresses = windows.map(window => window.address);
        }
        onMonitorsReceived: monitors => root.monitors = monitors
        onLayersReceived: layers => root.layers = layers
        onWorkspacesReceived: workspaces => {
            root.allWorkspaces = workspaces;
            root.workspaces = workspaces.filter(workspace => workspace.id >= 1 && workspace.id <= 100);
            let workspaceById = {};
            for (const workspace of root.workspaces)
                workspaceById[workspace.id] = workspace;
            root.workspaceById = workspaceById;
            root.workspaceIds = root.workspaces.map(workspace => workspace.id);
        }
        onActiveWorkspaceReceived: workspace => root.activeWorkspace = workspace
    }
}
