pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Quickshell.Hyprland
import "../../common"
import "../../services"
import "."

ColumnLayout {
    id: workspaceGrid

    property var workspaceLayout: ({})
    property var windowByAddress: ({})
    property int activeWorkspaceId: 1
    property real workspaceSpacing: 0
    property real workspaceImplicitWidth: 0
    property real workspaceImplicitHeight: 0
    property real workspaceNumberSize: 0
    property real scale: 1
    property bool glassMode: false
    property real glassShineOpacity: 0
    property real glassBorderOpacity: 0
    property real effectiveWorkspaceOpacity: 1
    property int draggingFromWorkspace: -1
    property int draggingTargetWorkspace: -1

    signal dragTargetEntered(int workspaceId)
    signal dragTargetExited(int workspaceId)

    // Calculate which rows have windows or current workspace
    readonly property var rowsWithContent: {
        if (!Config.options.overview.hideEmptyRows)
            return null;

        const layout = workspaceGrid.workspaceLayout;
        const workspacesShown = layout.rows * layout.columns;
        const firstWorkspace = layout.workspaceGroup * workspacesShown + 1 + layout.workspaceOffset;
        const lastWorkspace = (layout.workspaceGroup + 1) * workspacesShown + layout.workspaceOffset;
        const rows = new Set();

        // Add row containing current workspace
        if (workspaceGrid.activeWorkspaceId >= firstWorkspace && workspaceGrid.activeWorkspaceId <= lastWorkspace)
            rows.add(OverviewWorkspaceMath.workspaceRow(workspaceGrid.activeWorkspaceId, layout));

        // Add rows with windows
        for (const address in workspaceGrid.windowByAddress) {
            const workspaceId = workspaceGrid.windowByAddress[address]?.workspace?.id;
            if (workspaceId >= firstWorkspace && workspaceId <= lastWorkspace)
                rows.add(OverviewWorkspaceMath.workspaceRow(workspaceId, layout));
        }

        return rows;
    }

    spacing: workspaceGrid.workspaceSpacing

    Repeater {
        model: Config.options.overview.rows
        delegate: RowLayout {
            id: workspaceGridRow
            required property int index
            spacing: workspaceGrid.workspaceSpacing
            visible: !Config.options.overview.hideEmptyRows ||
                     (workspaceGrid.rowsWithContent && workspaceGrid.rowsWithContent.has(workspaceGridRow.index))
            height: visible ? implicitHeight : 0

            Repeater { // Workspace repeater
                model: Config.options.overview.columns
                Rectangle { // Workspace
                    id: workspace
                    required property int index
                    property int workspaceValue: OverviewWorkspaceMath.workspaceInCell(workspaceGridRow.index, workspace.index, workspaceGrid.workspaceLayout)
                    property color defaultWorkspaceColor: Appearance.colors.colLayer1
                    property color hoveredWorkspaceColor: ColorUtils.mix(workspace.defaultWorkspaceColor, Appearance.colors.colLayer1Hover, 0.1)
                    property color hoveredBorderColor: Appearance.colors.colLayer2Hover
                    property bool hoveredWhileDragging: false

                    implicitWidth: workspaceGrid.workspaceImplicitWidth
                    implicitHeight: workspaceGrid.workspaceImplicitHeight
                    color: ColorUtils.applyAlpha(
                        workspaceGrid.glassMode
                            ? ColorUtils.mix(workspace.hoveredWhileDragging ? workspace.hoveredWorkspaceColor : workspace.defaultWorkspaceColor, Appearance.colors.colLayer0, 0.46)
                            : (workspace.hoveredWhileDragging ? workspace.hoveredWorkspaceColor : workspace.defaultWorkspaceColor),
                        workspaceGrid.effectiveWorkspaceOpacity
                    )
                    radius: Appearance.rounding.screenRounding * workspaceGrid.scale
                    border.width: 2
                    border.color: workspace.hoveredWhileDragging
                        ? ColorUtils.applyAlpha(workspace.hoveredBorderColor, workspaceGrid.glassMode ? workspaceGrid.glassBorderOpacity : 1)
                        : "transparent"

                    Rectangle {
                        visible: workspaceGrid.glassMode
                        anchors.fill: parent
                        radius: parent.radius
                        color: "transparent"
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: ColorUtils.applyAlpha("#FFFFFF", workspaceGrid.glassShineOpacity * 0.22) }
                            GradientStop { position: 0.46; color: ColorUtils.applyAlpha("#FFFFFF", 0.0) }
                            GradientStop { position: 1.0; color: ColorUtils.applyAlpha("#000000", workspaceGrid.glassShineOpacity * 0.14) }
                        }
                    }

                    Rectangle {
                        visible: workspaceGrid.glassMode
                        anchors.fill: parent
                        anchors.margins: 1
                        radius: Math.max(parent.radius - 1, 0)
                        color: "transparent"
                        border.width: 1
                        border.color: ColorUtils.applyAlpha("#FFFFFF", workspaceGrid.glassBorderOpacity * 0.16)
                    }

                    StyledText {
                        anchors.centerIn: parent
                        text: workspace.workspaceValue
                        font {
                            pixelSize: workspaceGrid.workspaceNumberSize * workspaceGrid.scale
                            weight: Font.DemiBold
                            family: Appearance.font.family.expressive
                        }
                        color: ColorUtils.transparentize(Appearance.m3colors.m3onSurface, 0.3)
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton
                        onClicked: {
                            if (workspaceGrid.draggingTargetWorkspace === -1) {
                                GlobalStates.overviewOpen = false
                                Hyprland.dispatch(`workspace ${workspace.workspaceValue}`)
                            }
                        }
                    }

                    DropArea {
                        anchors.fill: parent
                        onEntered: {
                            workspaceGrid.dragTargetEntered(workspace.workspaceValue)
                            if (workspaceGrid.draggingFromWorkspace === workspace.workspaceValue) return;
                            workspace.hoveredWhileDragging = true
                        }
                        onExited: {
                            workspace.hoveredWhileDragging = false
                            workspaceGrid.dragTargetExited(workspace.workspaceValue)
                        }
                    }

                }
            }
        }
    }
}
