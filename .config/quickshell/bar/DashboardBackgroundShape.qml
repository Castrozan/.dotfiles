import QtQuick
import QtQuick.Shapes

ShapePath {
    id: dashboardBackgroundShapeRoot

    required property real dashboardX
    required property real dashboardY
    required property real dashboardWidth
    required property real dashboardHeight
    required property bool dashboardVisible

    readonly property real cornerRadius: 16
    readonly property real effectiveCornerRadius: Math.min(cornerRadius, dashboardWidth / 2, dashboardHeight / 2)
    readonly property bool shouldFlatten: dashboardHeight < cornerRadius * 2

    fillColor: dashboardVisible ? ThemeColors.backgroundSolid : "transparent"
    strokeWidth: -1

    startX: dashboardBackgroundShapeRoot.dashboardX
    startY: dashboardBackgroundShapeRoot.dashboardY

    PathLine {
        x: dashboardBackgroundShapeRoot.dashboardX + dashboardBackgroundShapeRoot.dashboardWidth
        y: dashboardBackgroundShapeRoot.dashboardY
    }

    PathLine {
        x: dashboardBackgroundShapeRoot.dashboardX + dashboardBackgroundShapeRoot.dashboardWidth
        y: dashboardBackgroundShapeRoot.dashboardY + dashboardBackgroundShapeRoot.dashboardHeight - dashboardBackgroundShapeRoot.effectiveCornerRadius
    }

    PathArc {
        x: dashboardBackgroundShapeRoot.dashboardX + dashboardBackgroundShapeRoot.dashboardWidth - dashboardBackgroundShapeRoot.effectiveCornerRadius
        y: dashboardBackgroundShapeRoot.dashboardY + dashboardBackgroundShapeRoot.dashboardHeight
        radiusX: dashboardBackgroundShapeRoot.effectiveCornerRadius
        radiusY: dashboardBackgroundShapeRoot.effectiveCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: dashboardBackgroundShapeRoot.dashboardX + dashboardBackgroundShapeRoot.effectiveCornerRadius
        y: dashboardBackgroundShapeRoot.dashboardY + dashboardBackgroundShapeRoot.dashboardHeight
    }

    PathArc {
        x: dashboardBackgroundShapeRoot.dashboardX
        y: dashboardBackgroundShapeRoot.dashboardY + dashboardBackgroundShapeRoot.dashboardHeight - dashboardBackgroundShapeRoot.effectiveCornerRadius
        radiusX: dashboardBackgroundShapeRoot.effectiveCornerRadius
        radiusY: dashboardBackgroundShapeRoot.effectiveCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: dashboardBackgroundShapeRoot.dashboardX
        y: dashboardBackgroundShapeRoot.dashboardY
    }
}
