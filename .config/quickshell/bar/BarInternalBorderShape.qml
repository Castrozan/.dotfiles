import QtQuick
import QtQuick.Shapes

ShapePath {
    id: barInternalBorderRoot

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

    required property real launcherX
    required property real launcherWidth
    required property real launcherHeight

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

    readonly property real clampedExtensionBottomEdge: bottomCornerMerged ? Math.min(extensionBottomEdge, barHeight - stripThickness) : extensionBottomEdge
    readonly property real clampedExtensionTopEdge: topCornerMerged ? Math.max(extensionTopEdge, stripThickness) : extensionTopEdge

    readonly property bool bottomFullyMerged: bottomCornerMerged && mergedBottomArcRadius <= 0
    readonly property bool topFullyMerged: topCornerMerged && mergedTopArcRadius <= 0

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

    readonly property bool hasLauncher: launcherHeight > 0
    readonly property real launcherTopEdge: barHeight - stripThickness - launcherHeight
    readonly property real launcherRightEdge: launcherX + launcherWidth
    readonly property real launcherCornerArcRadius: Math.min(junctionRadius, launcherWidth / 2, launcherHeight / 2)
    readonly property real launcherLeftJunctionArcRadius: Math.min(junctionRadius, launcherHeight, Math.max(0, launcherX - bottomEdgeTargetX))
    readonly property real launcherRightJunctionArcRadius: Math.min(junctionRadius, launcherHeight, Math.max(0, (screenWidth - stripThickness - innerCornerRadius) - launcherRightEdge))

    fillColor: "transparent"
    strokeColor: ThemeColors.accent
    strokeWidth: 2
    joinStyle: ShapePath.RoundJoin
    capStyle: ShapePath.RoundCap

    startX: topEdgeTargetX
    startY: stripThickness

    PathLine {
        x: barInternalBorderRoot.dashboardX - barInternalBorderRoot.dashboardLeftJunctionArcRadius
        y: barInternalBorderRoot.stripThickness
    }

    PathArc {
        x: barInternalBorderRoot.dashboardX
        y: barInternalBorderRoot.stripThickness + barInternalBorderRoot.dashboardLeftJunctionArcRadius
        radiusX: barInternalBorderRoot.dashboardLeftJunctionArcRadius
        radiusY: barInternalBorderRoot.dashboardLeftJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: barInternalBorderRoot.dashboardX
        y: barInternalBorderRoot.dashboardBottomEdge - barInternalBorderRoot.dashboardCornerArcRadius
    }

    PathArc {
        x: barInternalBorderRoot.dashboardX + barInternalBorderRoot.dashboardCornerArcRadius
        y: barInternalBorderRoot.dashboardBottomEdge
        radiusX: barInternalBorderRoot.dashboardCornerArcRadius
        radiusY: barInternalBorderRoot.dashboardCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: barInternalBorderRoot.dashboardRightEdge - barInternalBorderRoot.dashboardCornerArcRadius
        y: barInternalBorderRoot.dashboardBottomEdge
    }

    PathArc {
        x: barInternalBorderRoot.dashboardRightEdge
        y: barInternalBorderRoot.dashboardBottomEdge - barInternalBorderRoot.dashboardCornerArcRadius
        radiusX: barInternalBorderRoot.dashboardCornerArcRadius
        radiusY: barInternalBorderRoot.dashboardCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: barInternalBorderRoot.dashboardRightEdge
        y: barInternalBorderRoot.stripThickness + barInternalBorderRoot.dashboardRightJunctionArcRadius
    }

    PathArc {
        x: barInternalBorderRoot.dashboardRightEdge + barInternalBorderRoot.dashboardRightJunctionArcRadius
        y: barInternalBorderRoot.stripThickness
        radiusX: barInternalBorderRoot.dashboardRightJunctionArcRadius
        radiusY: barInternalBorderRoot.dashboardRightJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: barInternalBorderRoot.screenWidth - barInternalBorderRoot.stripThickness - barInternalBorderRoot.innerCornerRadius
        y: barInternalBorderRoot.stripThickness
    }

    PathArc {
        x: barInternalBorderRoot.screenWidth - barInternalBorderRoot.stripThickness
        y: barInternalBorderRoot.stripThickness + barInternalBorderRoot.innerCornerRadius
        radiusX: barInternalBorderRoot.innerCornerRadius
        radiusY: barInternalBorderRoot.innerCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: barInternalBorderRoot.screenWidth - barInternalBorderRoot.stripThickness
        y: barInternalBorderRoot.barHeight - barInternalBorderRoot.stripThickness - barInternalBorderRoot.innerCornerRadius
    }

    PathArc {
        x: barInternalBorderRoot.screenWidth - barInternalBorderRoot.stripThickness - barInternalBorderRoot.innerCornerRadius
        y: barInternalBorderRoot.barHeight - barInternalBorderRoot.stripThickness
        radiusX: barInternalBorderRoot.innerCornerRadius
        radiusY: barInternalBorderRoot.innerCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: barInternalBorderRoot.launcherRightEdge + barInternalBorderRoot.launcherRightJunctionArcRadius
        y: barInternalBorderRoot.barHeight - barInternalBorderRoot.stripThickness
    }

    PathArc {
        x: barInternalBorderRoot.launcherRightEdge
        y: barInternalBorderRoot.barHeight - barInternalBorderRoot.stripThickness - barInternalBorderRoot.launcherRightJunctionArcRadius
        radiusX: barInternalBorderRoot.launcherRightJunctionArcRadius
        radiusY: barInternalBorderRoot.launcherRightJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: barInternalBorderRoot.launcherRightEdge
        y: barInternalBorderRoot.launcherTopEdge + barInternalBorderRoot.launcherCornerArcRadius
    }

    PathArc {
        x: barInternalBorderRoot.launcherRightEdge - barInternalBorderRoot.launcherCornerArcRadius
        y: barInternalBorderRoot.launcherTopEdge
        radiusX: barInternalBorderRoot.launcherCornerArcRadius
        radiusY: barInternalBorderRoot.launcherCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: barInternalBorderRoot.launcherX + barInternalBorderRoot.launcherCornerArcRadius
        y: barInternalBorderRoot.launcherTopEdge
    }

    PathArc {
        x: barInternalBorderRoot.launcherX
        y: barInternalBorderRoot.launcherTopEdge + barInternalBorderRoot.launcherCornerArcRadius
        radiusX: barInternalBorderRoot.launcherCornerArcRadius
        radiusY: barInternalBorderRoot.launcherCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: barInternalBorderRoot.launcherX
        y: barInternalBorderRoot.barHeight - barInternalBorderRoot.stripThickness - barInternalBorderRoot.launcherLeftJunctionArcRadius
    }

    PathArc {
        x: barInternalBorderRoot.launcherX - barInternalBorderRoot.launcherLeftJunctionArcRadius
        y: barInternalBorderRoot.barHeight - barInternalBorderRoot.stripThickness
        radiusX: barInternalBorderRoot.launcherLeftJunctionArcRadius
        radiusY: barInternalBorderRoot.launcherLeftJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: barInternalBorderRoot.bottomEdgeTargetX
        y: barInternalBorderRoot.barHeight - barInternalBorderRoot.stripThickness
    }

    PathArc {
        x: barInternalBorderRoot.bottomFullyMerged ? barInternalBorderRoot.bottomEdgeTargetX : barInternalBorderRoot.barWidth
        y: barInternalBorderRoot.bottomFullyMerged ? barInternalBorderRoot.clampedExtensionBottomEdge : (barInternalBorderRoot.barHeight - barInternalBorderRoot.stripThickness - barInternalBorderRoot.effectiveBottomLeftBarCornerRadius)
        radiusX: barInternalBorderRoot.effectiveBottomLeftBarCornerRadius
        radiusY: barInternalBorderRoot.effectiveBottomLeftBarCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: barInternalBorderRoot.bottomFullyMerged ? barInternalBorderRoot.bottomEdgeTargetX : barInternalBorderRoot.barWidth
        y: barInternalBorderRoot.clampedExtensionBottomEdge + barInternalBorderRoot.effectiveBottomJunctionArcRadius
    }

    PathArc {
        x: barInternalBorderRoot.bottomFullyMerged ? barInternalBorderRoot.bottomEdgeTargetX : (barInternalBorderRoot.barWidth + barInternalBorderRoot.effectiveBottomJunctionArcRadius)
        y: barInternalBorderRoot.clampedExtensionBottomEdge
        radiusX: barInternalBorderRoot.effectiveBottomJunctionArcRadius
        radiusY: barInternalBorderRoot.effectiveBottomJunctionArcRadius
        direction: barInternalBorderRoot.bottomCornerMerged ? PathArc.Clockwise : PathArc.Counterclockwise
    }

    PathLine {
        x: barInternalBorderRoot.extensionRight - barInternalBorderRoot.extensionCornerArcRadius
        y: barInternalBorderRoot.clampedExtensionBottomEdge
    }

    PathArc {
        x: barInternalBorderRoot.extensionRight
        y: barInternalBorderRoot.clampedExtensionBottomEdge - barInternalBorderRoot.extensionCornerArcRadius
        radiusX: barInternalBorderRoot.extensionCornerArcRadius
        radiusY: barInternalBorderRoot.extensionCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: barInternalBorderRoot.extensionRight
        y: barInternalBorderRoot.clampedExtensionTopEdge + barInternalBorderRoot.extensionCornerArcRadius
    }

    PathArc {
        x: barInternalBorderRoot.extensionRight - barInternalBorderRoot.extensionCornerArcRadius
        y: barInternalBorderRoot.clampedExtensionTopEdge
        radiusX: barInternalBorderRoot.extensionCornerArcRadius
        radiusY: barInternalBorderRoot.extensionCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: barInternalBorderRoot.topFullyMerged ? barInternalBorderRoot.topEdgeTargetX : (barInternalBorderRoot.barWidth + barInternalBorderRoot.effectiveTopJunctionArcRadius)
        y: barInternalBorderRoot.clampedExtensionTopEdge
    }

    PathArc {
        x: barInternalBorderRoot.topFullyMerged ? barInternalBorderRoot.topEdgeTargetX : barInternalBorderRoot.barWidth
        y: barInternalBorderRoot.topFullyMerged ? barInternalBorderRoot.clampedExtensionTopEdge : (barInternalBorderRoot.clampedExtensionTopEdge - barInternalBorderRoot.effectiveTopJunctionArcRadius)
        radiusX: barInternalBorderRoot.effectiveTopJunctionArcRadius
        radiusY: barInternalBorderRoot.effectiveTopJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: barInternalBorderRoot.topFullyMerged ? barInternalBorderRoot.topEdgeTargetX : barInternalBorderRoot.barWidth
        y: barInternalBorderRoot.stripThickness + barInternalBorderRoot.effectiveTopLeftBarCornerRadius
    }

    PathArc {
        x: barInternalBorderRoot.topEdgeTargetX
        y: barInternalBorderRoot.stripThickness
        radiusX: barInternalBorderRoot.effectiveTopLeftBarCornerRadius
        radiusY: barInternalBorderRoot.effectiveTopLeftBarCornerRadius
        direction: PathArc.Clockwise
    }
}
