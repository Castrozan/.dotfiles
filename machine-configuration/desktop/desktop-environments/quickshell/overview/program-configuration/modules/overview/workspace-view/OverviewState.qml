import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "../../../common"
import "../../../services"
import ".."

Scope {
    id: root
    required property var panelWindow
    readonly property HyprlandMonitor monitor: Hyprland.monitorFor(panelWindow.screen)
    readonly property var toplevels: ToplevelManager.toplevels
    readonly property int effectiveActiveWorkspaceId: Math.max(1, Math.min(100, monitor?.activeWorkspace?.id ?? 1))
    readonly property int workspacesShown: Config.options.overview.rows * Config.options.overview.columns
    readonly property bool useWorkspaceMap: Config.options.overview.useWorkspaceMap
    readonly property var workspaceMap: Config.options.overview.workspaceMap
    readonly property int workspaceOffset: useWorkspaceMap ? Number(workspaceMap[root.monitor?.id] ?? 0) : 0
    readonly property int workspaceGroup: Math.floor((effectiveActiveWorkspaceId - workspaceOffset - 1) / workspacesShown)
    property bool monitorIsFocused: (Hyprland.focusedMonitor?.name == monitor.name)
    property var windows: HyprlandData.windowList
    property var windowByAddress: HyprlandData.windowByAddress
    property var windowAddresses: HyprlandData.addresses
    property var workspaceIds: HyprlandData.workspaceIds
    property var monitorData: HyprlandData.monitors.find(m => m.id === root.monitor?.id)
    property real scale: Config.options.overview.scale
    property color activeBorderColor: Appearance.colors.colSecondary

    property real workspaceImplicitWidth: (monitorData?.transform % 2 === 1) ? ((monitor.height / monitor.scale - (monitorData?.reserved?.[0] ?? 0) - (monitorData?.reserved?.[2] ?? 0)) * root.scale) : ((monitor.width / monitor.scale - (monitorData?.reserved?.[0] ?? 0) - (monitorData?.reserved?.[2] ?? 0)) * root.scale)
    property real workspaceImplicitHeight: (monitorData?.transform % 2 === 1) ? ((monitor.width / monitor.scale - (monitorData?.reserved?.[1] ?? 0) - (monitorData?.reserved?.[3] ?? 0)) * root.scale) : ((monitor.height / monitor.scale - (monitorData?.reserved?.[1] ?? 0) - (monitorData?.reserved?.[3] ?? 0)) * root.scale)

    property real workspaceNumberMargin: 80
    property real workspaceNumberSize: Config.options.overview.workspaceNumberBaseSize * monitor.scale
    property int workspaceZ: 0
    property int windowZ: 1
    property int windowDraggingZ: 99999
    property real workspaceSpacing: Config.options.overview.workspaceSpacing
    property bool showSpecialWorkspaces: Config.options.overview.showSpecialWorkspaces
    property var configuredSpecialWorkspaces: Config.options.overview.specialWorkspaces ?? []
    property int specialWorkspaceColumns: Math.max(1, Config.options.overview.specialWorkspaceColumns)
    property real panelOpacity: Math.max(0, Math.min(1, Config.options.overview.effects.panelOpacity))
    property real workspaceOpacity: Math.max(0, Math.min(1, Config.options.overview.effects.workspaceOpacity))
    property bool glassMode: Config.options.overview.effects.glassMode
    property real glassTintStrength: Math.max(0, Math.min(1, Config.options.overview.effects.glassTintStrength))
    property real glassBorderOpacity: Math.max(0, Math.min(1, Config.options.overview.effects.glassBorderOpacity))
    property real glassShineOpacity: Math.max(0, Math.min(1, Config.options.overview.effects.glassShineOpacity))
    property real effectivePanelOpacity: glassMode ? Math.min(panelOpacity, 0.72) : panelOpacity
    property real effectiveWorkspaceOpacity: glassMode ? Math.min(workspaceOpacity, 0.62) : workspaceOpacity

    property int draggingFromWorkspace: -1
    property int draggingTargetWorkspace: -1
    property string draggingTargetSpecialWorkspace: ""
    property int previewRecaptureToken: 0
    property var allWorkspaces: HyprlandData.allWorkspaces
    property bool previewsEnabled: Config.options.overview.previewsEnabled
    property string previewModeRaw: Config.options.overview.previewMode
    property string previewMode: {
        const mode = `${previewModeRaw ?? "live"}`.trim().toLowerCase();
        return (mode === "event" || mode === "snapshot") ? "event" : "live";
    }
    property bool useEventPreviewRefresh: previewsEnabled && previewMode === "event"

    readonly property string createSpecialWorkspaceTarget: "__create_special_workspace__"
    readonly property var workspaceLayout: ({
            rows: Config.options.overview.rows,
            columns: Config.options.overview.columns,
            orderBottomUp: Config.options.overview.orderBottomUp,
            orderRightLeft: Config.options.overview.orderRightLeft,
            workspaceOffset: root.workspaceOffset,
            workspaceGroup: root.workspaceGroup
        })

    function stepWorkspace(delta) {
        if (!Number.isFinite(delta) || delta === 0)
            return;

        const currentId = monitor?.activeWorkspace?.id ?? effectiveActiveWorkspaceId;
        const minWorkspaceId = workspaceOffset + 1;
        let maxWorkspaceId = minWorkspaceId + workspacesShown - 1;
        for (const workspaceId of (workspaceIds ?? [])) {
            if (Number.isFinite(workspaceId) && workspaceId >= minWorkspaceId) {
                maxWorkspaceId = Math.max(maxWorkspaceId, workspaceId);
            }
        }
        maxWorkspaceId = Math.max(maxWorkspaceId, currentId);

        let targetId = currentId + delta;
        if (targetId < minWorkspaceId) {
            targetId = maxWorkspaceId;
        } else if (targetId > maxWorkspaceId) {
            targetId = minWorkspaceId;
        }
        Hyprland.dispatch(`workspace ${targetId}`);
    }

    property Component windowComponent: OverviewWindow {}
    property list<OverviewWindow> windowWidgets: []

    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (!GlobalStates.overviewOpen || !root.useEventPreviewRefresh)
                return;

            const eventName = `${event?.name ?? event?.event ?? event?.type ?? ""}`;
            if (eventName === "closewindow" || eventName === "openwindow" || eventName === "movewindow") {
                root.previewRecaptureToken += 1;
            }
        }
    }
}
