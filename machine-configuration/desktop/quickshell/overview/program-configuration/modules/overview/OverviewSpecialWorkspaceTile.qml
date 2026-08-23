pragma ComponentBehavior: Bound
import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import "../../common"
import "../../services"
import "."

Rectangle {
    id: specialWorkspaceTile

    required property string modelData
    property OverviewSpecialWorkspaceModel specialWorkspaceModel
    property var monitor
    property var widgetMonitorData
    property var windowByAddress: ({})
    property Item windowDragLayer
    property real scale: 1
    property real workspaceImplicitWidth: 0
    property real workspaceImplicitHeight: 0
    property bool glassMode: false
    property real glassBorderOpacity: 0
    property real effectiveWorkspaceOpacity: 1
    property string createSpecialWorkspaceTarget: ""
    property int draggingTargetWorkspace: -1
    property string draggingTargetSpecialWorkspace: ""
    property int windowDraggingZ: 0
    property int previewRecaptureToken: 0

    signal dragTargetEntered(string specialWorkspaceName)
    signal dragTargetExited(string specialWorkspaceName)
    signal windowDragStarted()
    signal windowDragFinished()

    readonly property string specialName: specialWorkspaceTile.modelData
    readonly property var specialGeometry: specialWorkspaceTile.specialWorkspaceModel.specialWorkspaceGeometry(specialWorkspaceTile.specialName)
    readonly property color baseColor: ColorUtils.mix(Appearance.colors.colLayer1, Appearance.colors.colLayer0, 0.52)
    readonly property bool hasRenderableGeometry: Number.isFinite(specialWorkspaceTile.specialGeometry?.width)
        && Number.isFinite(specialWorkspaceTile.specialGeometry?.height)
        && specialWorkspaceTile.specialGeometry.width > 0
        && specialWorkspaceTile.specialGeometry.height > 0
    readonly property real geometryWidth: specialWorkspaceTile.hasRenderableGeometry ? specialWorkspaceTile.specialGeometry.width : Math.max(1, specialWorkspaceTile.workspaceImplicitWidth / specialWorkspaceTile.scale)
    readonly property real geometryHeight: specialWorkspaceTile.hasRenderableGeometry ? specialWorkspaceTile.specialGeometry.height : Math.max(1, specialWorkspaceTile.workspaceImplicitHeight / specialWorkspaceTile.scale)
    readonly property real fitScale: specialWorkspaceTile.hasRenderableGeometry ? Math.min(width / specialWorkspaceTile.geometryWidth, height / specialWorkspaceTile.geometryHeight) : specialWorkspaceTile.scale
    readonly property real contentWidth: specialWorkspaceTile.hasRenderableGeometry ? (specialWorkspaceTile.geometryWidth * specialWorkspaceTile.fitScale) : width
    readonly property real contentHeight: specialWorkspaceTile.hasRenderableGeometry ? (specialWorkspaceTile.geometryHeight * specialWorkspaceTile.fitScale) : height
    readonly property real contentOffsetX: Math.max(0, (width - specialWorkspaceTile.contentWidth) / 2)
    readonly property real contentOffsetY: Math.max(0, (height - specialWorkspaceTile.contentHeight) / 2)

    implicitWidth: specialWorkspaceTile.specialWorkspaceModel.tileWidth
    implicitHeight: specialWorkspaceTile.specialWorkspaceModel.tileHeight
    radius: Appearance.rounding.screenRounding * specialWorkspaceTile.scale
    clip: true
    color: ColorUtils.applyAlpha(
        specialWorkspaceTile.glassMode
            ? ColorUtils.mix(specialWorkspaceTile.baseColor, Appearance.colors.colLayer0, 0.44)
            : specialWorkspaceTile.baseColor,
        specialWorkspaceTile.effectiveWorkspaceOpacity
    )
    border.width: 1
    border.color: ColorUtils.applyAlpha(Appearance.colors.colLayer2Border, specialWorkspaceTile.glassMode ? specialWorkspaceTile.glassBorderOpacity : 0.75)

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onClicked: {
            if (specialWorkspaceTile.draggingTargetWorkspace === -1 && !specialWorkspaceTile.draggingTargetSpecialWorkspace) {
                GlobalStates.overviewOpen = false;
                Hyprland.dispatch(`togglespecialworkspace ${specialWorkspaceTile.specialName}`);
            }
        }
    }

    DropArea {
        anchors.fill: parent
        onEntered: specialWorkspaceTile.dragTargetEntered(specialWorkspaceTile.specialName)
        onExited: specialWorkspaceTile.dragTargetExited(specialWorkspaceTile.specialName)
    }

    Item {
        id: specialWorkspaceContent
        x: specialWorkspaceTile.contentOffsetX
        y: specialWorkspaceTile.contentOffsetY
        width: specialWorkspaceTile.contentWidth
        height: specialWorkspaceTile.contentHeight
        clip: true

        Repeater {
            model: ScriptModel {
                values: {
                    if (!specialWorkspaceTile.hasRenderableGeometry)
                        return [];
                    return ToplevelManager.toplevels.values.filter((toplevel) => {
                        const address = `0x${toplevel.HyprlandToplevel.address}`;
                        const win = specialWorkspaceTile.windowByAddress[address];
                        if ((win?.monitor ?? -1) !== (specialWorkspaceTile.monitor?.id ?? -1))
                            return false;
                        return specialWorkspaceTile.specialWorkspaceModel.specialWorkspaceName(win) === specialWorkspaceTile.specialName;
                    }).sort((a, b) => {
                        const addrA = `0x${a.HyprlandToplevel.address}`;
                        const addrB = `0x${b.HyprlandToplevel.address}`;
                        return addrA.localeCompare(addrB);
                    });
                }
            }
            delegate: OverviewSpecialWindow {
                id: specialWindow
                specialWorkspaceModel: specialWorkspaceTile.specialWorkspaceModel
                windowByAddress: specialWorkspaceTile.windowByAddress
                homeParent: specialWorkspaceContent
                windowDragLayer: specialWorkspaceTile.windowDragLayer
                homeSpecialWorkspaceName: specialWorkspaceTile.specialName
                createSpecialWorkspaceTarget: specialWorkspaceTile.createSpecialWorkspaceTarget
                draggingTargetWorkspace: specialWorkspaceTile.draggingTargetWorkspace
                draggingTargetSpecialWorkspace: specialWorkspaceTile.draggingTargetSpecialWorkspace
                windowDraggingZ: specialWorkspaceTile.windowDraggingZ
                widgetMonitorData: specialWorkspaceTile.widgetMonitorData
                widgetMonitorId: specialWorkspaceTile.monitor.id
                scale: specialWorkspaceTile.scale
                recaptureToken: specialWorkspaceTile.previewRecaptureToken
                availableWorkspaceWidth: specialWorkspaceContent.width
                availableWorkspaceHeight: specialWorkspaceContent.height
                positionBaseX: Number.isFinite(specialWorkspaceTile.specialGeometry?.x) ? specialWorkspaceTile.specialGeometry.x : ((specialWindow.monitor?.x ?? 0) + (specialWindow.monitor?.reserved?.[0] ?? 0))
                positionBaseY: Number.isFinite(specialWorkspaceTile.specialGeometry?.y) ? specialWorkspaceTile.specialGeometry.y : ((specialWindow.monitor?.y ?? 0) + (specialWindow.monitor?.reserved?.[1] ?? 0))
                geometryScaleX: specialWorkspaceTile.fitScale / specialWorkspaceTile.scale
                geometryScaleY: specialWorkspaceTile.fitScale / specialWorkspaceTile.scale
                onDragStarted: specialWorkspaceTile.windowDragStarted()
                onDragFinished: specialWorkspaceTile.windowDragFinished()
            }
        }
    }
}
