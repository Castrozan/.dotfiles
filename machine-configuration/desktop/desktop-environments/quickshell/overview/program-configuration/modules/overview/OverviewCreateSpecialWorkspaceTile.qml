import QtQuick
import Quickshell.Hyprland
import "../../common"
import "../../services"
import "."

Rectangle {
    id: createSpecialWorkspaceTile

    property OverviewSpecialWorkspaceModel specialWorkspaceModel
    property real scale: 1
    property bool glassMode: false
    property real effectiveWorkspaceOpacity: 1
    property color activeBorderColor: "transparent"
    property string createSpecialWorkspaceTarget: ""
    property string draggingTargetSpecialWorkspace: ""

    signal dragTargetEntered(string specialWorkspaceName)
    signal dragTargetExited(string specialWorkspaceName)

    readonly property bool isDragTarget: createSpecialWorkspaceTile.draggingTargetSpecialWorkspace === createSpecialWorkspaceTile.createSpecialWorkspaceTarget

    implicitWidth: createSpecialWorkspaceTile.specialWorkspaceModel.tileWidth
    implicitHeight: createSpecialWorkspaceTile.specialWorkspaceModel.tileHeight
    radius: Appearance.rounding.screenRounding * createSpecialWorkspaceTile.scale
    color: ColorUtils.applyAlpha(
        createSpecialWorkspaceTile.glassMode
            ? ColorUtils.mix(Appearance.colors.colSecondaryContainer, Appearance.colors.colLayer1, 0.58)
            : ColorUtils.mix(Appearance.colors.colLayer2, Appearance.colors.colLayer1, 0.55),
        createSpecialWorkspaceTile.isDragTarget ? 0.90 : createSpecialWorkspaceTile.effectiveWorkspaceOpacity
    )
    border.width: 1
    border.color: createSpecialWorkspaceTile.isDragTarget
        ? ColorUtils.applyAlpha(createSpecialWorkspaceTile.activeBorderColor, 0.96)
        : ColorUtils.applyAlpha(Appearance.colors.colSecondary, 0.46)

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: Math.max(parent.radius - 1, 0)
        color: "transparent"
        border.width: 1
        border.color: ColorUtils.applyAlpha("#FFFFFF", createSpecialWorkspaceTile.glassMode ? 0.12 : 0.08)
    }

    Column {
        anchors.centerIn: parent
        spacing: 0

        StyledText {
            anchors.horizontalCenter: parent.horizontalCenter
            text: createSpecialWorkspaceTile.isDragTarget ? "Release" : "+"
            font.family: Appearance.font.family.expressive
            font.pixelSize: createSpecialWorkspaceTile.isDragTarget
                ? Appearance.font.pixelSize.larger * createSpecialWorkspaceTile.scale
                : Appearance.font.pixelSize.huge * 1.25 * createSpecialWorkspaceTile.scale
            font.weight: Font.DemiBold
            color: ColorUtils.applyAlpha(Appearance.colors.colOnLayer1, 0.92)
            horizontalAlignment: Text.AlignHCenter
        }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onClicked: {
            const createdName = OverviewWorkspaceMath.nextSpecialWorkspaceName(createSpecialWorkspaceTile.specialWorkspaceModel.visibleSpecialWorkspaces);
            GlobalStates.overviewOpen = false;
            Hyprland.dispatch(`togglespecialworkspace ${createdName}`);
        }
    }

    DropArea {
        anchors.fill: parent
        onEntered: createSpecialWorkspaceTile.dragTargetEntered(createSpecialWorkspaceTile.createSpecialWorkspaceTarget)
        onExited: createSpecialWorkspaceTile.dragTargetExited(createSpecialWorkspaceTile.createSpecialWorkspaceTarget)
    }
}
