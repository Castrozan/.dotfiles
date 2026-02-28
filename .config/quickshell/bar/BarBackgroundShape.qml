import QtQuick
import QtQuick.Shapes

ShapePath {
    id: shapePathRoot

    required property real barWidth
    required property real barHeight
    required property real screenWidth
    required property real junctionRadius
    required property real extensionY
    required property real extensionHeight
    required property real extensionWidth

    required property real dashboardX
    required property real dashboardWidth
    required property real dashboardHeight

    readonly property real stripThickness: barWidth / 3

    readonly property real innerCornerRadius: Math.min(junctionRadius, stripThickness)

    readonly property real barRightEdgeStartY: stripThickness + innerCornerRadius
    readonly property real barRightEdgeEndY: barHeight - stripThickness - innerCornerRadius

    readonly property real extensionTopEdge: extensionY
    readonly property real extensionBottomEdge: extensionY + extensionHeight

    readonly property bool hasExtension: extensionWidth > 0

    readonly property real topJunctionAvailableSpace: Math.max(0, extensionTopEdge - barRightEdgeStartY)
    readonly property real bottomJunctionAvailableSpace: Math.max(0, barRightEdgeEndY - extensionBottomEdge)

    readonly property real topJunctionArcRadius: Math.min(junctionRadius, extensionWidth, topJunctionAvailableSpace)
    readonly property real bottomJunctionArcRadius: Math.min(junctionRadius, extensionWidth, bottomJunctionAvailableSpace)

    readonly property real extensionCornerArcRadius: Math.min(junctionRadius, extensionWidth, extensionHeight / 2)
    readonly property real extensionRight: barWidth + extensionWidth

    readonly property bool bottomCornerMerged: hasExtension && (extensionBottomEdge + junctionRadius >= barRightEdgeEndY)
    readonly property bool topCornerMerged: hasExtension && (extensionTopEdge - junctionRadius <= barRightEdgeStartY)

    readonly property real mergedBottomArcRadius: Math.max(0, (barHeight - stripThickness) - extensionBottomEdge)
    readonly property real mergedTopArcRadius: Math.max(0, extensionTopEdge - stripThickness)

    readonly property bool bottomFullyMerged: bottomCornerMerged && mergedBottomArcRadius <= 0
    readonly property bool topFullyMerged: topCornerMerged && mergedTopArcRadius <= 0

    readonly property real clampedExtensionBottomEdge: bottomCornerMerged ? Math.min(extensionBottomEdge, barHeight - stripThickness) : extensionBottomEdge
    readonly property real clampedExtensionTopEdge: topCornerMerged ? Math.max(extensionTopEdge, stripThickness) : extensionTopEdge

    readonly property real effectiveBottomLeftBarCornerRadius: bottomCornerMerged ? 0 : innerCornerRadius
    readonly property real effectiveTopLeftBarCornerRadius: topCornerMerged ? 0 : innerCornerRadius
    readonly property real effectiveBottomJunctionArcRadius: bottomCornerMerged ? mergedBottomArcRadius : bottomJunctionArcRadius
    readonly property real effectiveTopJunctionArcRadius: topCornerMerged ? mergedTopArcRadius : topJunctionArcRadius

    readonly property real bottomEdgeTargetX: bottomFullyMerged ? (extensionRight - extensionCornerArcRadius) : (barWidth + effectiveBottomLeftBarCornerRadius)
    readonly property real topEdgeTargetX: topFullyMerged ? (extensionRight - extensionCornerArcRadius) : (barWidth + effectiveTopLeftBarCornerRadius)

    readonly property bool hasDashboard: dashboardHeight > 0
    readonly property real dashboardBottomEdge: stripThickness + dashboardHeight
    readonly property real dashboardRightEdge: dashboardX + dashboardWidth
    readonly property real dashboardCornerArcRadius: Math.min(junctionRadius, dashboardWidth / 2, dashboardHeight / 2)
    readonly property real dashboardLeftJunctionArcRadius: Math.min(junctionRadius, dashboardHeight, Math.max(0, dashboardX - topEdgeTargetX))
    readonly property real dashboardRightJunctionArcRadius: Math.min(junctionRadius, dashboardHeight, Math.max(0, (screenWidth - stripThickness - innerCornerRadius) - dashboardRightEdge))

    fillColor: ThemeColors.background
    strokeWidth: -1

    startX: 0
    startY: 0

    PathLine {
        x: shapePathRoot.screenWidth
        y: 0
    }

    PathLine {
        x: shapePathRoot.screenWidth
        y: shapePathRoot.barHeight
    }

    PathLine {
        x: 0
        y: shapePathRoot.barHeight
    }

    PathLine {
        x: 0
        y: 0
    }

    PathMove {
        x: shapePathRoot.topEdgeTargetX
        y: shapePathRoot.stripThickness
    }

    PathLine {
        x: shapePathRoot.dashboardX - shapePathRoot.dashboardLeftJunctionArcRadius
        y: shapePathRoot.stripThickness
    }

    PathArc {
        x: shapePathRoot.dashboardX
        y: shapePathRoot.stripThickness + shapePathRoot.dashboardLeftJunctionArcRadius
        radiusX: shapePathRoot.dashboardLeftJunctionArcRadius
        radiusY: shapePathRoot.dashboardLeftJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.dashboardX
        y: shapePathRoot.dashboardBottomEdge - shapePathRoot.dashboardCornerArcRadius
    }

    PathArc {
        x: shapePathRoot.dashboardX + shapePathRoot.dashboardCornerArcRadius
        y: shapePathRoot.dashboardBottomEdge
        radiusX: shapePathRoot.dashboardCornerArcRadius
        radiusY: shapePathRoot.dashboardCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: shapePathRoot.dashboardRightEdge - shapePathRoot.dashboardCornerArcRadius
        y: shapePathRoot.dashboardBottomEdge
    }

    PathArc {
        x: shapePathRoot.dashboardRightEdge
        y: shapePathRoot.dashboardBottomEdge - shapePathRoot.dashboardCornerArcRadius
        radiusX: shapePathRoot.dashboardCornerArcRadius
        radiusY: shapePathRoot.dashboardCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: shapePathRoot.dashboardRightEdge
        y: shapePathRoot.stripThickness + shapePathRoot.dashboardRightJunctionArcRadius
    }

    PathArc {
        x: shapePathRoot.dashboardRightEdge + shapePathRoot.dashboardRightJunctionArcRadius
        y: shapePathRoot.stripThickness
        radiusX: shapePathRoot.dashboardRightJunctionArcRadius
        radiusY: shapePathRoot.dashboardRightJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.screenWidth - shapePathRoot.stripThickness - shapePathRoot.innerCornerRadius
        y: shapePathRoot.stripThickness
    }

    PathArc {
        x: shapePathRoot.screenWidth - shapePathRoot.stripThickness
        y: shapePathRoot.stripThickness + shapePathRoot.innerCornerRadius
        radiusX: shapePathRoot.innerCornerRadius
        radiusY: shapePathRoot.innerCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.screenWidth - shapePathRoot.stripThickness
        y: shapePathRoot.barHeight - shapePathRoot.stripThickness - shapePathRoot.innerCornerRadius
    }

    PathArc {
        x: shapePathRoot.screenWidth - shapePathRoot.stripThickness - shapePathRoot.innerCornerRadius
        y: shapePathRoot.barHeight - shapePathRoot.stripThickness
        radiusX: shapePathRoot.innerCornerRadius
        radiusY: shapePathRoot.innerCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.bottomEdgeTargetX
        y: shapePathRoot.barHeight - shapePathRoot.stripThickness
    }

    PathArc {
        x: shapePathRoot.bottomFullyMerged ? shapePathRoot.bottomEdgeTargetX : shapePathRoot.barWidth
        y: shapePathRoot.bottomFullyMerged ? shapePathRoot.clampedExtensionBottomEdge : (shapePathRoot.barHeight - shapePathRoot.stripThickness - shapePathRoot.effectiveBottomLeftBarCornerRadius)
        radiusX: shapePathRoot.effectiveBottomLeftBarCornerRadius
        radiusY: shapePathRoot.effectiveBottomLeftBarCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.bottomFullyMerged ? shapePathRoot.bottomEdgeTargetX : shapePathRoot.barWidth
        y: shapePathRoot.clampedExtensionBottomEdge + shapePathRoot.effectiveBottomJunctionArcRadius
    }

    PathArc {
        x: shapePathRoot.bottomFullyMerged ? shapePathRoot.bottomEdgeTargetX : (shapePathRoot.barWidth + shapePathRoot.effectiveBottomJunctionArcRadius)
        y: shapePathRoot.clampedExtensionBottomEdge
        radiusX: shapePathRoot.effectiveBottomJunctionArcRadius
        radiusY: shapePathRoot.effectiveBottomJunctionArcRadius
        direction: shapePathRoot.bottomCornerMerged ? PathArc.Clockwise : PathArc.Counterclockwise
    }

    PathLine {
        x: shapePathRoot.extensionRight - shapePathRoot.extensionCornerArcRadius
        y: shapePathRoot.clampedExtensionBottomEdge
    }

    PathArc {
        x: shapePathRoot.extensionRight
        y: shapePathRoot.clampedExtensionBottomEdge - shapePathRoot.extensionCornerArcRadius
        radiusX: shapePathRoot.extensionCornerArcRadius
        radiusY: shapePathRoot.extensionCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: shapePathRoot.extensionRight
        y: shapePathRoot.clampedExtensionTopEdge + shapePathRoot.extensionCornerArcRadius
    }

    PathArc {
        x: shapePathRoot.extensionRight - shapePathRoot.extensionCornerArcRadius
        y: shapePathRoot.clampedExtensionTopEdge
        radiusX: shapePathRoot.extensionCornerArcRadius
        radiusY: shapePathRoot.extensionCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: shapePathRoot.topFullyMerged ? shapePathRoot.topEdgeTargetX : (shapePathRoot.barWidth + shapePathRoot.effectiveTopJunctionArcRadius)
        y: shapePathRoot.clampedExtensionTopEdge
    }

    PathArc {
        x: shapePathRoot.topFullyMerged ? shapePathRoot.topEdgeTargetX : shapePathRoot.barWidth
        y: shapePathRoot.topFullyMerged ? shapePathRoot.clampedExtensionTopEdge : (shapePathRoot.clampedExtensionTopEdge - shapePathRoot.effectiveTopJunctionArcRadius)
        radiusX: shapePathRoot.effectiveTopJunctionArcRadius
        radiusY: shapePathRoot.effectiveTopJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.topFullyMerged ? shapePathRoot.topEdgeTargetX : shapePathRoot.barWidth
        y: shapePathRoot.stripThickness + shapePathRoot.effectiveTopLeftBarCornerRadius
    }

    PathArc {
        x: shapePathRoot.topEdgeTargetX
        y: shapePathRoot.stripThickness
        radiusX: shapePathRoot.effectiveTopLeftBarCornerRadius
        radiusY: shapePathRoot.effectiveTopLeftBarCornerRadius
        direction: PathArc.Clockwise
    }
}
