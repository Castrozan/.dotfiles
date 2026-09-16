import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "../../../common"
import "../../../services"
import ".."

OverviewWindow {
    id: window
    required property OverviewState overviewState
    required property OverviewSpecialWorkspaceModel specialWorkspaces
    required property var modelData
    required property int index
    property int monitorId: window.windowData?.monitor
    property var monitor: HyprlandData.monitors.find(m => m.id === window.monitorId)
    property var address: `0x${window.modelData.HyprlandToplevel.address}`
    windowData: window.overviewState.windowByAddress[window.address]
    toplevel: window.modelData
    monitorData: window.monitor
    widgetMonitorData: window.overviewState.monitorData
    scale: window.overviewState.scale
    availableWorkspaceWidth: window.overviewState.workspaceImplicitWidth
    availableWorkspaceHeight: window.overviewState.workspaceImplicitHeight
    widgetMonitorId: window.overviewState.monitor.id
    recaptureToken: window.overviewState.previewRecaptureToken

    property bool atInitPosition: (initX == x && initY == y)

    property int workspaceColIndex: OverviewWorkspaceMath.workspaceColumn(window.windowData?.workspace.id, window.overviewState.workspaceLayout)
    property int workspaceRowIndex: OverviewWorkspaceMath.workspaceRow(window.windowData?.workspace.id, window.overviewState.workspaceLayout)
    xOffset: (window.overviewState.workspaceImplicitWidth + window.overviewState.workspaceSpacing) * workspaceColIndex
    yOffset: (window.overviewState.workspaceImplicitHeight + window.overviewState.workspaceSpacing) * workspaceRowIndex

    Timer {
        id: updateWindowPosition
        interval: Config.options.hacks.arbitraryRaceConditionDelay
        repeat: false
        running: false
        onTriggered: {
            window.x = Math.round(Math.max((window.windowData?.at[0] - (window.monitor?.x ?? 0) - (window.monitorData?.reserved?.[0] ?? 0)) * window.overviewState.scale * window.widthRatio, 0) + window.xOffset);
            window.y = Math.round(Math.max((window.windowData?.at[1] - (window.monitor?.y ?? 0) - (window.monitorData?.reserved?.[1] ?? 0)) * window.overviewState.scale * window.heightRatio, 0) + window.yOffset);
        }
    }

    z: atInitPosition ? (window.overviewState.windowZ + index) : window.overviewState.windowDraggingZ
    Drag.hotSpot.x: window.targetWindowWidth / 2
    Drag.hotSpot.y: window.targetWindowHeight / 2
    MouseArea {
        id: dragArea
        anchors.fill: parent
        hoverEnabled: true
        onEntered: window.hovered = true
        onExited: window.hovered = false
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
        drag.target: parent
        onPressed: mouse => {
            window.overviewState.draggingFromWorkspace = window.windowData?.workspace.id;
            window.overviewState.draggingTargetSpecialWorkspace = "";
            window.pressed = true;
            window.Drag.active = true;
            window.Drag.source = window;
            window.Drag.hotSpot.x = mouse.x;
            window.Drag.hotSpot.y = mouse.y;
        }
        onReleased: {
            const targetWorkspace = window.overviewState.draggingTargetWorkspace;
            const targetSpecialWorkspace = window.overviewState.draggingTargetSpecialWorkspace;
            window.pressed = false;
            window.Drag.active = false;
            window.overviewState.draggingFromWorkspace = -1;
            window.overviewState.draggingTargetWorkspace = -1;
            window.overviewState.draggingTargetSpecialWorkspace = "";
            if (targetSpecialWorkspace === window.overviewState.createSpecialWorkspaceTarget) {
                const createdName = OverviewWorkspaceMath.nextSpecialWorkspaceName(window.specialWorkspaces.visibleSpecialWorkspaces);
                Hyprland.dispatch(`movetoworkspacesilent special:${createdName}, address:${window.windowData?.address}`);
                updateWindowPosition.restart();
            } else if (targetSpecialWorkspace && targetSpecialWorkspace !== window.specialWorkspaces.specialWorkspaceName(window.windowData)) {
                Hyprland.dispatch(`movetoworkspacesilent special:${targetSpecialWorkspace}, address:${window.windowData?.address}`);
                updateWindowPosition.restart();
            } else if (targetWorkspace !== -1 && targetWorkspace !== window.windowData?.workspace.id) {
                Hyprland.dispatch(`movetoworkspacesilent ${targetWorkspace}, address:${window.windowData?.address}`);
                updateWindowPosition.restart();
            } else {
                window.x = window.initX;
                window.y = window.initY;
            }
        }
        onClicked: event => {
            if (!window.windowData)
                return;

            if (event.button === Qt.LeftButton) {
                GlobalStates.overviewOpen = false;
                Hyprland.dispatch(`focuswindow address:${window.windowData.address}`);
                event.accepted = true;
            } else if (event.button === Qt.MiddleButton) {
                Hyprland.dispatch(`closewindow address:${window.windowData.address}`);
                event.accepted = true;
            }
        }

        StyledToolTip {
            extraVisibleCondition: false
            alternativeVisibleCondition: dragArea.containsMouse && !window.Drag.active
            text: `${window.windowData?.title ?? "Unknown"}\n[${window.windowData?.class ?? "unknown"}] ${window.windowData?.xwayland ? "[XWayland] " : ""}`
        }
    }
}
