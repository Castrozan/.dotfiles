import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "../../../common"
import "../../../services"
import ".."

Item { // Windows & focused workspace indicator
    id: windowSpace
    required property OverviewState overviewState
    required property OverviewSpecialWorkspaceModel specialWorkspaces
    anchors.centerIn: parent

    WheelHandler {
        target: null
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: event => {
            const deltaY = event.angleDelta.y;
            if (!deltaY)
                return;
            windowSpace.overviewState.stepWorkspace(deltaY > 0 ? -1 : 1);
            event.accepted = true;
        }
    }

    Repeater {
        // Window repeater
        model: ScriptModel {
            values: {
                return ToplevelManager.toplevels.values.filter(toplevel => {
                    const address = `0x${toplevel.HyprlandToplevel.address}`;
                    var win = windowSpace.overviewState.windowByAddress[address];
                    if (windowSpace.specialWorkspaces.isSpecialWorkspace(win))
                        return false;
                    const minWorkspace = windowSpace.overviewState.workspaceGroup * windowSpace.overviewState.workspacesShown + 1 + windowSpace.overviewState.workspaceOffset;
                    const maxWorkspace = (windowSpace.overviewState.workspaceGroup + 1) * windowSpace.overviewState.workspacesShown + windowSpace.overviewState.workspaceOffset;
                    const inWorkspaceGroup = (minWorkspace <= win?.workspace?.id && win?.workspace?.id <= maxWorkspace);
                    return inWorkspaceGroup;
                }).sort((a, b) => {
                    // Proper stacking order based on Hyprland's window properties
                    const addrA = `0x${a.HyprlandToplevel.address}`;
                    const addrB = `0x${b.HyprlandToplevel.address}`;
                    const winA = windowSpace.overviewState.windowByAddress[addrA];
                    const winB = windowSpace.overviewState.windowByAddress[addrB];

                    // 1. Pinned windows are always on top
                    if (winA?.pinned !== winB?.pinned) {
                        return winA?.pinned ? 1 : -1;
                    }

                    // 2. Floating windows above tiled windows
                    if (winA?.floating !== winB?.floating) {
                        return winA?.floating ? 1 : -1;
                    }

                    // 3. Within same category, sort by focus history
                    // Lower focusHistoryID = more recently focused = higher in stack
                    return (winB?.focusHistoryID ?? 0) - (winA?.focusHistoryID ?? 0);
                });
            }
        }
        delegate: OverviewDraggableWindow {
            overviewState: windowSpace.overviewState
            specialWorkspaces: windowSpace.specialWorkspaces
        }
    }

    Rectangle { // Focused workspace indicator
        id: focusedWorkspaceIndicator
        property int activeWorkspaceRowIndex: OverviewWorkspaceMath.workspaceRow(windowSpace.overviewState.effectiveActiveWorkspaceId, windowSpace.overviewState.workspaceLayout)
        property int activeWorkspaceColIndex: OverviewWorkspaceMath.workspaceColumn(windowSpace.overviewState.effectiveActiveWorkspaceId, windowSpace.overviewState.workspaceLayout)
        x: (windowSpace.overviewState.workspaceImplicitWidth + windowSpace.overviewState.workspaceSpacing) * activeWorkspaceColIndex
        y: (windowSpace.overviewState.workspaceImplicitHeight + windowSpace.overviewState.workspaceSpacing) * activeWorkspaceRowIndex
        z: windowSpace.overviewState.windowZ
        width: windowSpace.overviewState.workspaceImplicitWidth
        height: windowSpace.overviewState.workspaceImplicitHeight
        color: "transparent"
        radius: Appearance.rounding.screenRounding * windowSpace.overviewState.scale
        border.width: 2
        border.color: windowSpace.overviewState.activeBorderColor
        Behavior on x {
            animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
        }
        Behavior on y {
            animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
        }
    }
}
