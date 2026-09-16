import QtQuick
import QtQuick.Layouts
import "../../common"
import "."
import "workspace-view"

Item {
    id: root
    required property var panelWindow

    OverviewState {
        id: workspaceState
        panelWindow: root.panelWindow
    }

    implicitWidth: overviewBackground.implicitWidth + Appearance.sizes.elevationMargin * 2
    implicitHeight: overviewBackground.implicitHeight + Appearance.sizes.elevationMargin * 2

    OverviewSpecialWorkspaceModel {
        id: specialWorkspaceData
        monitor: workspaceState.monitor
        windowByAddress: workspaceState.windowByAddress
        allWorkspaces: workspaceState.allWorkspaces
        configuredSpecialWorkspaces: workspaceState.configuredSpecialWorkspaces
        showSpecialWorkspaces: workspaceState.showSpecialWorkspaces
        columnCount: workspaceState.specialWorkspaceColumns
        scale: workspaceState.scale
        workspaceSpacing: workspaceState.workspaceSpacing
        tileHeight: workspaceState.workspaceImplicitHeight
        sectionWidth: workspaceGrid.implicitWidth
        workspaceGridHeight: workspaceGrid.implicitHeight
    }

    StyledRectangularShadow {
        target: overviewBackground
    }
    OverviewBackground {
        id: overviewBackground
        overviewState: workspaceState
        implicitWidth: contentLayout.implicitWidth + padding * 2
        implicitHeight: contentLayout.implicitHeight + padding * 2

        ColumnLayout { // Workspaces
            id: contentLayout

            z: workspaceState.workspaceZ
            anchors.centerIn: parent
            spacing: workspaceState.workspaceSpacing

            OverviewWorkspaceGrid {
                id: workspaceGrid
                workspaceLayout: workspaceState.workspaceLayout
                windowByAddress: workspaceState.windowByAddress
                activeWorkspaceId: workspaceState.effectiveActiveWorkspaceId
                workspaceSpacing: workspaceState.workspaceSpacing
                workspaceImplicitWidth: workspaceState.workspaceImplicitWidth
                workspaceImplicitHeight: workspaceState.workspaceImplicitHeight
                workspaceNumberSize: workspaceState.workspaceNumberSize
                scale: workspaceState.scale
                glassMode: workspaceState.glassMode
                glassShineOpacity: workspaceState.glassShineOpacity
                glassBorderOpacity: workspaceState.glassBorderOpacity
                effectiveWorkspaceOpacity: workspaceState.effectiveWorkspaceOpacity
                draggingFromWorkspace: workspaceState.draggingFromWorkspace
                draggingTargetWorkspace: workspaceState.draggingTargetWorkspace
                onDragTargetEntered: workspaceId => {
                    workspaceState.draggingTargetWorkspace = workspaceId;
                    workspaceState.draggingTargetSpecialWorkspace = "";
                }
                onDragTargetExited: workspaceId => {
                    if (workspaceState.draggingTargetWorkspace === workspaceId)
                        workspaceState.draggingTargetWorkspace = -1;
                }
            }

            Item {
                visible: workspaceState.showSpecialWorkspaces && specialWorkspaceData.hasSpecialWorkspaceSection
                implicitWidth: 1
                implicitHeight: specialWorkspaceData.stripGap
            }

            OverviewSpecialWorkspaceStrip {
                visible: workspaceState.showSpecialWorkspaces && specialWorkspaceData.hasSpecialWorkspaceSection
                specialWorkspaceModel: specialWorkspaceData
                monitor: workspaceState.monitor
                widgetMonitorData: workspaceState.monitorData
                windowByAddress: workspaceState.windowByAddress
                windowDragLayer: specialWindowDragLayer
                scale: workspaceState.scale
                workspaceSpacing: workspaceState.workspaceSpacing
                workspaceImplicitWidth: workspaceState.workspaceImplicitWidth
                workspaceImplicitHeight: workspaceState.workspaceImplicitHeight
                glassMode: workspaceState.glassMode
                glassBorderOpacity: workspaceState.glassBorderOpacity
                effectivePanelOpacity: workspaceState.effectivePanelOpacity
                effectiveWorkspaceOpacity: workspaceState.effectiveWorkspaceOpacity
                activeBorderColor: workspaceState.activeBorderColor
                createSpecialWorkspaceTarget: workspaceState.createSpecialWorkspaceTarget
                draggingTargetWorkspace: workspaceState.draggingTargetWorkspace
                draggingTargetSpecialWorkspace: workspaceState.draggingTargetSpecialWorkspace
                windowDraggingZ: workspaceState.windowDraggingZ
                previewRecaptureToken: workspaceState.previewRecaptureToken
                onDragTargetEntered: specialWorkspaceName => {
                    workspaceState.draggingTargetWorkspace = -1;
                    workspaceState.draggingTargetSpecialWorkspace = specialWorkspaceName;
                }
                onDragTargetExited: specialWorkspaceName => {
                    if (workspaceState.draggingTargetSpecialWorkspace === specialWorkspaceName)
                        workspaceState.draggingTargetSpecialWorkspace = "";
                }
                onWindowDragStarted: {
                    workspaceState.draggingFromWorkspace = -1;
                    workspaceState.draggingTargetSpecialWorkspace = "";
                }
                onWindowDragFinished: {
                    workspaceState.draggingFromWorkspace = -1;
                    workspaceState.draggingTargetWorkspace = -1;
                    workspaceState.draggingTargetSpecialWorkspace = "";
                }
            }
        }

        OverviewWindowLayer {
            overviewState: workspaceState
            specialWorkspaces: specialWorkspaceData
            implicitWidth: contentLayout.implicitWidth
            implicitHeight: contentLayout.implicitHeight
        }

        Item {
            id: specialWindowDragLayer
            anchors.fill: parent
            z: workspaceState.windowDraggingZ + 1
        }
    }
}
