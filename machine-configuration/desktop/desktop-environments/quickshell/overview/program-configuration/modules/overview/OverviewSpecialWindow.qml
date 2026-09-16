import QtQuick
import Quickshell.Hyprland
import "../../common"
import "../../services"
import "."

OverviewWindow {
    id: specialWindow

    required property var modelData
    property OverviewSpecialWorkspaceModel specialWorkspaceModel
    property var windowByAddress: ({})
    property Item homeParent
    property Item windowDragLayer
    property string homeSpecialWorkspaceName: ""
    property string createSpecialWorkspaceTarget: ""
    property int draggingTargetWorkspace: -1
    property string draggingTargetSpecialWorkspace: ""
    property int windowDraggingZ: 0

    signal dragStarted()
    signal dragFinished()

    property var address: `0x${specialWindow.modelData.HyprlandToplevel.address}`
    property int monitorId: specialWindow.windowData?.monitor
    property var monitor: HyprlandData.monitors.find(m => m.id === specialWindow.monitorId)

    windowData: specialWindow.windowByAddress[specialWindow.address]
    toplevel: specialWindow.modelData
    monitorData: specialWindow.monitor
    xOffset: 0
    yOffset: 0
    restrictToWorkspace: false
    animateSize: false
    z: specialWindow.specialWorkspaceModel.specialWindowZ(specialWindow.windowData)

    function moveToDragLayer() {
        const mapped = specialWindow.mapToItem(specialWindow.windowDragLayer, 0, 0);
        specialWindow.suspendPositionAnimation = true;
        specialWindow.parent = specialWindow.windowDragLayer;
        specialWindow.x = mapped.x;
        specialWindow.y = mapped.y;
        specialWindow.z = specialWindow.windowDraggingZ + 1;
        Qt.callLater(() => specialWindow.suspendPositionAnimation = false);
    }

    function returnToHomeParent() {
        specialWindow.suspendPositionAnimation = true;
        specialWindow.parent = specialWindow.homeParent;
        specialWindow.z = specialWindow.specialWorkspaceModel.specialWindowZ(specialWindow.windowData);
        Qt.callLater(() => specialWindow.suspendPositionAnimation = false);
    }

    MouseArea {
        id: specialDragArea
        anchors.fill: parent
        hoverEnabled: true
        onEntered: specialWindow.hovered = true
        onExited: specialWindow.hovered = false
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
        drag.target: parent
        onPressed: (mouse) => {
            specialWindow.dragStarted()
            specialWindow.pressed = true
            specialWindow.dragInProgress = true
            specialWindow.Drag.source = specialWindow
            specialWindow.Drag.hotSpot.x = mouse.x
            specialWindow.Drag.hotSpot.y = mouse.y
            specialWindow.moveToDragLayer()
            specialWindow.Drag.active = true
        }
        onReleased: {
            const targetWorkspace = specialWindow.draggingTargetWorkspace
            const targetSpecialWorkspace = specialWindow.draggingTargetSpecialWorkspace
            specialWindow.pressed = false
            specialWindow.Drag.active = false
            specialWindow.dragInProgress = false
            specialWindow.dragFinished()
            if (targetSpecialWorkspace === specialWindow.createSpecialWorkspaceTarget) {
                const createdName = OverviewWorkspaceMath.nextSpecialWorkspaceName(specialWindow.specialWorkspaceModel.visibleSpecialWorkspaces)
                Hyprland.dispatch(`movetoworkspacesilent special:${createdName}, address:${specialWindow.windowData?.address}`)
            }
            else if (targetSpecialWorkspace && targetSpecialWorkspace !== specialWindow.homeSpecialWorkspaceName) {
                Hyprland.dispatch(`movetoworkspacesilent special:${targetSpecialWorkspace}, address:${specialWindow.windowData?.address}`)
            }
            else if (targetWorkspace !== -1) {
                Hyprland.dispatch(`movetoworkspacesilent ${targetWorkspace}, address:${specialWindow.windowData?.address}`)
            }
            specialWindow.returnToHomeParent()
            specialWindow.x = specialWindow.initX
            specialWindow.y = specialWindow.initY
        }
        onClicked: (event) => {
            if (!specialWindow.windowData)
                return;
            if (event.button === Qt.LeftButton) {
                GlobalStates.overviewOpen = false;
                Hyprland.dispatch(`focuswindow address:${specialWindow.windowData.address}`);
                event.accepted = true;
            } else if (event.button === Qt.MiddleButton) {
                Hyprland.dispatch(`closewindow address:${specialWindow.windowData.address}`);
                event.accepted = true;
            }
        }

        StyledToolTip {
            extraVisibleCondition: false
            alternativeVisibleCondition: specialDragArea.containsMouse && !specialWindow.Drag.active
            text: `${specialWindow.windowData?.title ?? "Unknown"}\n[${specialWindow.windowData?.class ?? "unknown"}] ${specialWindow.windowData?.xwayland ? "[XWayland] " : ""}`
        }
    }
}
