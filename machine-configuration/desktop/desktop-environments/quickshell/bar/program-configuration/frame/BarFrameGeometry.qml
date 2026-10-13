import QtQuick

QtObject {
    required property real leftBarWidth
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

    readonly property real stripThickness: 0
    readonly property real windowBorderWidth: 2
    readonly property real windowCornerRadius: 12
    readonly property real windowBorderInset: windowBorderWidth / 2
    readonly property real topWindowBorderCenterY: windowBorderInset
    readonly property real bottomWindowBorderCenterY: barHeight - windowBorderInset
    readonly property real rightWindowBorderCenterX: screenWidth - windowBorderInset
    readonly property real leftBarBorderRightEdge: leftBarWidth + windowBorderInset

    readonly property real innerCornerRadius: Math.min(junctionRadius, stripThickness)
    readonly property real leftBarCornerArcRadius: Math.min(junctionRadius, leftBarWidth, Math.max(0, bottomWindowBorderCenterY - topWindowBorderCenterY) / 2)
    readonly property real topLeftBarCornerArcRadius: hasExtension ? Math.min(leftBarCornerArcRadius, Math.max(0, clampedExtensionTopEdge - topWindowBorderCenterY) / 2) : leftBarCornerArcRadius
    readonly property real bottomLeftBarCornerArcRadius: hasExtension ? Math.min(leftBarCornerArcRadius, Math.max(0, bottomWindowBorderCenterY - clampedExtensionBottomEdge) / 2) : leftBarCornerArcRadius

    readonly property real barRightEdgeStartY: topWindowBorderCenterY + topLeftBarCornerArcRadius
    readonly property real barRightEdgeEndY: bottomWindowBorderCenterY - bottomLeftBarCornerArcRadius

    readonly property real extensionTopEdge: extensionY
    readonly property real extensionBottomEdge: extensionY + extensionHeight

    readonly property bool hasExtension: extensionWidth > 0 && extensionHeight > 0

    readonly property real topJunctionAvailableSpace: Math.max(0, clampedExtensionTopEdge - barRightEdgeStartY)
    readonly property real bottomJunctionAvailableSpace: Math.max(0, barRightEdgeEndY - clampedExtensionBottomEdge)

    readonly property real topJunctionArcRadius: Math.min(junctionRadius, extensionWidth, topJunctionAvailableSpace)
    readonly property real bottomJunctionArcRadius: Math.min(junctionRadius, extensionWidth, bottomJunctionAvailableSpace)

    readonly property real extensionCornerArcRadius: Math.min(junctionRadius, extensionWidth, Math.max(0, clampedExtensionBottomEdge - clampedExtensionTopEdge) / 2)
    readonly property real extensionRight: leftBarWidth + extensionWidth
    readonly property real extensionBorderRightEdge: extensionRight + windowBorderInset

    readonly property bool bottomCornerMerged: hasExtension && (extensionBottomEdge + windowBorderInset + junctionRadius >= barRightEdgeEndY)
    readonly property bool topCornerMerged: hasExtension && (extensionTopEdge - windowBorderInset - junctionRadius <= barRightEdgeStartY)

    readonly property real mergedBottomArcRadius: Math.max(0, bottomWindowBorderCenterY - extensionBottomEdge - windowBorderInset)
    readonly property real mergedTopArcRadius: Math.max(0, extensionTopEdge - windowBorderInset - topWindowBorderCenterY)

    readonly property real clampedExtensionTopEdge: Math.min(bottomWindowBorderCenterY, Math.max(extensionTopEdge - windowBorderInset, topWindowBorderCenterY))
    readonly property real clampedExtensionBottomEdge: Math.max(clampedExtensionTopEdge, Math.min(extensionBottomEdge + windowBorderInset, bottomWindowBorderCenterY))

    readonly property bool bottomFullyMerged: bottomCornerMerged && mergedBottomArcRadius <= 0
    readonly property bool topFullyMerged: topCornerMerged && mergedTopArcRadius <= 0

    readonly property real effectiveBottomLeftBarCornerRadius: bottomFullyMerged ? 0 : bottomLeftBarCornerArcRadius
    readonly property real effectiveTopLeftBarCornerRadius: topFullyMerged ? 0 : topLeftBarCornerArcRadius
    readonly property real effectiveBottomJunctionArcRadius: bottomFullyMerged ? 0 : bottomJunctionArcRadius
    readonly property real effectiveTopJunctionArcRadius: topFullyMerged ? 0 : topJunctionArcRadius

    readonly property real bottomEdgeTargetX: bottomFullyMerged ? (extensionBorderRightEdge + extensionCornerArcRadius) : (leftBarBorderRightEdge + effectiveBottomLeftBarCornerRadius)
    readonly property real topEdgeTargetX: topFullyMerged ? (extensionBorderRightEdge + extensionCornerArcRadius) : (leftBarBorderRightEdge + effectiveTopLeftBarCornerRadius)

    readonly property bool hasDashboard: dashboardHeight > 0
    readonly property real dashboardBottomEdge: stripThickness + dashboardHeight
    readonly property real dashboardRightEdge: dashboardX + dashboardWidth
    readonly property real dashboardBorderLeftEdge: dashboardX - windowBorderInset
    readonly property real dashboardBorderRightEdge: dashboardRightEdge + windowBorderInset
    readonly property real dashboardBorderBottomEdge: Math.max(topWindowBorderCenterY, dashboardBottomEdge + windowBorderInset)
    readonly property real dashboardCornerArcRadius: Math.min(junctionRadius, (dashboardWidth + windowBorderWidth) / 2, (dashboardBorderBottomEdge - topWindowBorderCenterY) / 2)
    readonly property real dashboardJunctionAvailableHeight: Math.max(0, dashboardBorderBottomEdge - topWindowBorderCenterY - dashboardCornerArcRadius)
    readonly property real dashboardLeftJunctionArcRadius: Math.min(junctionRadius, dashboardJunctionAvailableHeight, Math.max(0, dashboardBorderLeftEdge - topEdgeTargetX))
    readonly property real dashboardRightJunctionArcRadius: Math.min(junctionRadius, dashboardJunctionAvailableHeight, Math.max(0, rightWindowBorderCenterX - dashboardBorderRightEdge))

    required property real rightPanelY
    required property real rightPanelWidth
    required property real rightPanelHeight

    readonly property bool hasRightPanel: rightPanelWidth > 0 && rightPanelHeight > 0
    readonly property real rightStripLeftEdge: screenWidth - stripThickness
    readonly property real rightPanelLeftEdge: rightStripLeftEdge - rightPanelWidth
    readonly property real rightPanelBorderLeftEdge: rightPanelLeftEdge - windowBorderInset
    readonly property real rightPanelTopEdge: rightPanelY
    readonly property real rightPanelBottomEdge: rightPanelY + rightPanelHeight

    readonly property real rightStripTopCornerStartY: topWindowBorderCenterY + innerCornerRadius
    readonly property real rightStripBottomCornerStartY: bottomWindowBorderCenterY - innerCornerRadius

    readonly property real rightPanelTopJunctionAvailableSpace: Math.max(0, clampedRightPanelTopEdge - rightStripTopCornerStartY)
    readonly property real rightPanelBottomJunctionAvailableSpace: Math.max(0, rightStripBottomCornerStartY - clampedRightPanelBottomEdge)

    readonly property real rightPanelTopJunctionArcRadius: hasRightPanel ? Math.min(junctionRadius, rightPanelWidth / 2, rightPanelTopJunctionAvailableSpace) : 0
    readonly property real rightPanelBottomJunctionArcRadius: hasRightPanel ? Math.min(junctionRadius, rightPanelWidth / 2, rightPanelBottomJunctionAvailableSpace) : 0

    readonly property real rightPanelCornerArcRadius: hasRightPanel ? Math.min(junctionRadius, rightPanelWidth / 2, Math.max(0, clampedRightPanelBottomEdge - clampedRightPanelTopEdge) / 2) : 0

    readonly property bool rightPanelTopCornerMerged: hasRightPanel && (rightPanelTopEdge - windowBorderInset - junctionRadius <= rightStripTopCornerStartY)
    readonly property bool rightPanelBottomCornerMerged: hasRightPanel && (rightPanelBottomEdge + windowBorderInset + junctionRadius >= rightStripBottomCornerStartY)

    readonly property real rightPanelMergedTopArcRadius: Math.max(0, rightPanelTopEdge - windowBorderInset - topWindowBorderCenterY)
    readonly property real rightPanelMergedBottomArcRadius: Math.max(0, bottomWindowBorderCenterY - rightPanelBottomEdge - windowBorderInset)

    readonly property bool rightPanelTopFullyMerged: rightPanelTopCornerMerged && rightPanelMergedTopArcRadius <= 0
    readonly property bool rightPanelBottomFullyMerged: rightPanelBottomCornerMerged && rightPanelMergedBottomArcRadius <= 0

    readonly property real effectiveRightPanelTopJunctionArcRadius: rightPanelTopFullyMerged ? 0 : rightPanelTopJunctionArcRadius
    readonly property real effectiveRightPanelBottomJunctionArcRadius: rightPanelBottomFullyMerged ? 0 : rightPanelBottomJunctionArcRadius

    readonly property real effectiveRightTopInnerCornerRadius: rightPanelTopCornerMerged ? 0 : innerCornerRadius
    readonly property real effectiveRightBottomInnerCornerRadius: rightPanelBottomCornerMerged ? 0 : innerCornerRadius

    readonly property real clampedRightPanelTopEdge: Math.min(bottomWindowBorderCenterY, Math.max(rightPanelTopEdge - windowBorderInset, topWindowBorderCenterY))
    readonly property real clampedRightPanelBottomEdge: Math.max(clampedRightPanelTopEdge, Math.min(rightPanelBottomEdge + windowBorderInset, bottomWindowBorderCenterY))

    readonly property bool hasLauncher: launcherHeight > 0
    readonly property real launcherTopEdge: barHeight - stripThickness - launcherHeight
    readonly property real launcherRightEdge: launcherX + launcherWidth
    readonly property real launcherBorderLeftEdge: launcherX - windowBorderInset
    readonly property real launcherBorderRightEdge: launcherRightEdge + windowBorderInset
    readonly property real launcherBorderTopEdge: Math.min(bottomWindowBorderCenterY, launcherTopEdge - windowBorderInset)
    readonly property real launcherCornerArcRadius: Math.min(junctionRadius, (launcherWidth + windowBorderWidth) / 2, (bottomWindowBorderCenterY - launcherBorderTopEdge) / 2)
    readonly property real launcherJunctionAvailableHeight: Math.max(0, bottomWindowBorderCenterY - launcherBorderTopEdge - launcherCornerArcRadius)
    readonly property real launcherLeftJunctionArcRadius: Math.min(junctionRadius, launcherJunctionAvailableHeight, Math.max(0, launcherBorderLeftEdge - bottomEdgeTargetX))
    readonly property real launcherRightJunctionArcRadius: Math.min(junctionRadius, launcherJunctionAvailableHeight, Math.max(0, rightWindowBorderCenterX - launcherBorderRightEdge))
}
