import QtQuick
import QtQuick.Shapes

ShapePath {
    id: dashboardBorderShapeRoot

    required property real dashboardX
    required property real dashboardY
    required property real dashboardWidth
    required property real dashboardHeight
    required property bool dashboardVisible

    readonly property real cornerRadius: 16
    readonly property real effectiveCornerRadius: Math.min(cornerRadius, dashboardWidth / 2, dashboardHeight / 2)

    fillColor: "transparent"
    strokeColor: dashboardVisible ? ThemeColors.accent : "transparent"
    strokeWidth: 2
    joinStyle: ShapePath.RoundJoin
    capStyle: ShapePath.RoundCap

    startX: dashboardBorderShapeRoot.dashboardX
    startY: dashboardBorderShapeRoot.dashboardY

    PathLine {
        x: dashboardBorderShapeRoot.dashboardX + dashboardBorderShapeRoot.dashboardWidth
        y: dashboardBorderShapeRoot.dashboardY
    }

    PathLine {
        x: dashboardBorderShapeRoot.dashboardX + dashboardBorderShapeRoot.dashboardWidth
        y: dashboardBorderShapeRoot.dashboardY + dashboardBorderShapeRoot.dashboardHeight - dashboardBorderShapeRoot.effectiveCornerRadius
    }

    PathArc {
        x: dashboardBorderShapeRoot.dashboardX + dashboardBorderShapeRoot.dashboardWidth - dashboardBorderShapeRoot.effectiveCornerRadius
        y: dashboardBorderShapeRoot.dashboardY + dashboardBorderShapeRoot.dashboardHeight
        radiusX: dashboardBorderShapeRoot.effectiveCornerRadius
        radiusY: dashboardBorderShapeRoot.effectiveCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: dashboardBorderShapeRoot.dashboardX + dashboardBorderShapeRoot.effectiveCornerRadius
        y: dashboardBorderShapeRoot.dashboardY + dashboardBorderShapeRoot.dashboardHeight
    }

    PathArc {
        x: dashboardBorderShapeRoot.dashboardX
        y: dashboardBorderShapeRoot.dashboardY + dashboardBorderShapeRoot.dashboardHeight - dashboardBorderShapeRoot.effectiveCornerRadius
        radiusX: dashboardBorderShapeRoot.effectiveCornerRadius
        radiusY: dashboardBorderShapeRoot.effectiveCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: dashboardBorderShapeRoot.dashboardX
        y: dashboardBorderShapeRoot.dashboardY
    }
}
