pragma ComponentBehavior: Bound
import QtQuick
import "../../common"
import "."

Item {
    id: strip

    property OverviewSpecialWorkspaceModel specialWorkspaceModel
    property var monitor
    property var widgetMonitorData
    property var windowByAddress: ({})
    property Item windowDragLayer
    property real scale: 1
    property real workspaceSpacing: 0
    property real workspaceImplicitWidth: 0
    property real workspaceImplicitHeight: 0
    property bool glassMode: false
    property real glassBorderOpacity: 0
    property real effectivePanelOpacity: 1
    property real effectiveWorkspaceOpacity: 1
    property color activeBorderColor: "transparent"
    property string createSpecialWorkspaceTarget: ""
    property int draggingTargetWorkspace: -1
    property string draggingTargetSpecialWorkspace: ""
    property int windowDraggingZ: 0
    property int previewRecaptureToken: 0

    signal dragTargetEntered(string specialWorkspaceName)
    signal dragTargetExited(string specialWorkspaceName)
    signal windowDragStarted()
    signal windowDragFinished()

    implicitWidth: strip.specialWorkspaceModel.sectionWidth
    implicitHeight: strip.specialWorkspaceModel.stripHeight

    Rectangle {
        anchors.fill: parent
        radius: Appearance.rounding.normal * strip.scale
        color: ColorUtils.applyAlpha(
            strip.glassMode
                ? ColorUtils.mix(Appearance.colors.colLayer0, Appearance.colors.colLayer1, 0.70)
                : Appearance.colors.colLayer1,
            strip.glassMode ? Math.min(0.74, strip.effectivePanelOpacity) : strip.effectiveWorkspaceOpacity
        )
        border.width: 1
        border.color: ColorUtils.applyAlpha(Appearance.colors.colLayer2Border, strip.glassMode ? strip.glassBorderOpacity : 0.65)

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: Math.max(18 * strip.scale, strip.specialWorkspaceModel.stripPadding + strip.specialWorkspaceModel.stripTitleHeight * 0.8)
            radius: parent.radius
            color: ColorUtils.applyAlpha(Appearance.colors.colSecondary, strip.glassMode ? 0.12 : 0.08)
        }

        StyledText {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.leftMargin: strip.specialWorkspaceModel.stripPadding
            anchors.topMargin: strip.specialWorkspaceModel.stripPadding
            text: "Special Workspaces"
            font.family: Appearance.font.family.title
            font.pixelSize: strip.specialWorkspaceModel.stripTitleHeight
            font.weight: Font.DemiBold
            color: ColorUtils.applyAlpha(Appearance.colors.colOnLayer1, 0.84)
        }

        Grid {
            x: strip.specialWorkspaceModel.tileGridOffsetX
            y: strip.specialWorkspaceModel.tileGridTop
            width: strip.specialWorkspaceModel.tileGridUsedWidth
            columns: strip.specialWorkspaceModel.effectiveColumnCount
            rowSpacing: strip.workspaceSpacing
            columnSpacing: strip.workspaceSpacing

            Repeater {
                model: strip.specialWorkspaceModel.visibleSpecialWorkspaces
                delegate: OverviewSpecialWorkspaceTile {
                    specialWorkspaceModel: strip.specialWorkspaceModel
                    monitor: strip.monitor
                    widgetMonitorData: strip.widgetMonitorData
                    windowByAddress: strip.windowByAddress
                    windowDragLayer: strip.windowDragLayer
                    scale: strip.scale
                    workspaceImplicitWidth: strip.workspaceImplicitWidth
                    workspaceImplicitHeight: strip.workspaceImplicitHeight
                    glassMode: strip.glassMode
                    glassBorderOpacity: strip.glassBorderOpacity
                    effectiveWorkspaceOpacity: strip.effectiveWorkspaceOpacity
                    createSpecialWorkspaceTarget: strip.createSpecialWorkspaceTarget
                    draggingTargetWorkspace: strip.draggingTargetWorkspace
                    draggingTargetSpecialWorkspace: strip.draggingTargetSpecialWorkspace
                    windowDraggingZ: strip.windowDraggingZ
                    previewRecaptureToken: strip.previewRecaptureToken
                    onDragTargetEntered: specialWorkspaceName => strip.dragTargetEntered(specialWorkspaceName)
                    onDragTargetExited: specialWorkspaceName => strip.dragTargetExited(specialWorkspaceName)
                    onWindowDragStarted: strip.windowDragStarted()
                    onWindowDragFinished: strip.windowDragFinished()
                }
            }

            OverviewCreateSpecialWorkspaceTile {
                specialWorkspaceModel: strip.specialWorkspaceModel
                scale: strip.scale
                glassMode: strip.glassMode
                effectiveWorkspaceOpacity: strip.effectiveWorkspaceOpacity
                activeBorderColor: strip.activeBorderColor
                createSpecialWorkspaceTarget: strip.createSpecialWorkspaceTarget
                draggingTargetSpecialWorkspace: strip.draggingTargetSpecialWorkspace
                onDragTargetEntered: specialWorkspaceName => strip.dragTargetEntered(specialWorkspaceName)
                onDragTargetExited: specialWorkspaceName => strip.dragTargetExited(specialWorkspaceName)
            }
        }
    }
}
