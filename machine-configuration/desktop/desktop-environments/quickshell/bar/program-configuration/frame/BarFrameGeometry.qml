import QtQuick

QtObject {
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

    required property real rightPanelY
    required property real rightPanelWidth
    required property real rightPanelHeight

    readonly property bool hasRightPanel: rightPanelWidth > 0 && rightPanelHeight > 0
    readonly property real rightStripLeftEdge: screenWidth - stripThickness
    readonly property real rightPanelLeftEdge: rightStripLeftEdge - rightPanelWidth
    readonly property real rightPanelTopEdge: rightPanelY
    readonly property real rightPanelBottomEdge: rightPanelY + rightPanelHeight

    readonly property real rightStripTopCornerStartY: stripThickness + innerCornerRadius
    readonly property real rightStripBottomCornerStartY: barHeight - stripThickness - innerCornerRadius

    readonly property real rightPanelTopJunctionAvailableSpace: Math.max(0, rightPanelTopEdge - rightStripTopCornerStartY)
    readonly property real rightPanelBottomJunctionAvailableSpace: Math.max(0, rightStripBottomCornerStartY - rightPanelBottomEdge)

    readonly property real rightPanelTopJunctionArcRadius: hasRightPanel ? Math.min(junctionRadius, rightPanelWidth / 2, rightPanelTopJunctionAvailableSpace) : 0
    readonly property real rightPanelBottomJunctionArcRadius: hasRightPanel ? Math.min(junctionRadius, rightPanelWidth / 2, rightPanelBottomJunctionAvailableSpace) : 0

    readonly property real rightPanelCornerArcRadius: hasRightPanel ? Math.min(junctionRadius, rightPanelWidth / 2, rightPanelHeight / 2) : 0

    readonly property bool rightPanelTopCornerMerged: hasRightPanel && (rightPanelTopEdge - junctionRadius <= rightStripTopCornerStartY)
    readonly property bool rightPanelBottomCornerMerged: hasRightPanel && (rightPanelBottomEdge + junctionRadius >= rightStripBottomCornerStartY)

    readonly property real rightPanelMergedTopArcRadius: Math.max(0, rightPanelTopEdge - stripThickness)
    readonly property real rightPanelMergedBottomArcRadius: Math.max(0, (barHeight - stripThickness) - rightPanelBottomEdge)

    readonly property bool rightPanelTopFullyMerged: rightPanelTopCornerMerged && rightPanelMergedTopArcRadius <= 0
    readonly property bool rightPanelBottomFullyMerged: rightPanelBottomCornerMerged && rightPanelMergedBottomArcRadius <= 0

    readonly property real effectiveRightPanelTopJunctionArcRadius: rightPanelTopCornerMerged ? rightPanelMergedTopArcRadius : rightPanelTopJunctionArcRadius
    readonly property real effectiveRightPanelBottomJunctionArcRadius: rightPanelBottomCornerMerged ? rightPanelMergedBottomArcRadius : rightPanelBottomJunctionArcRadius

    readonly property real effectiveRightTopInnerCornerRadius: rightPanelTopCornerMerged ? 0 : innerCornerRadius
    readonly property real effectiveRightBottomInnerCornerRadius: rightPanelBottomCornerMerged ? 0 : innerCornerRadius

    readonly property real clampedRightPanelTopEdge: rightPanelTopCornerMerged ? Math.max(rightPanelTopEdge, stripThickness) : rightPanelTopEdge
    readonly property real clampedRightPanelBottomEdge: rightPanelBottomCornerMerged ? Math.min(rightPanelBottomEdge, barHeight - stripThickness) : rightPanelBottomEdge

    readonly property bool hasLauncher: launcherHeight > 0
    readonly property real launcherTopEdge: barHeight - stripThickness - launcherHeight
    readonly property real launcherRightEdge: launcherX + launcherWidth
    readonly property real launcherCornerArcRadius: Math.min(junctionRadius, launcherWidth / 2, launcherHeight / 2)
    readonly property real launcherLeftJunctionArcRadius: Math.min(junctionRadius, launcherHeight, Math.max(0, launcherX - bottomEdgeTargetX))
    readonly property real launcherRightJunctionArcRadius: Math.min(junctionRadius, launcherHeight, Math.max(0, (screenWidth - stripThickness - innerCornerRadius) - launcherRightEdge))
}
