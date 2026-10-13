import QtQuick

QtObject {
    id: contourRoot

    required property BarFrameGeometry geometry

    readonly property PathMove borderStart: PathMove {
        x: contourRoot.geometry.rightPanelTopFullyMerged ? contourRoot.geometry.rightPanelBorderLeftEdge - contourRoot.geometry.rightPanelCornerArcRadius : contourRoot.geometry.rightWindowBorderCenterX
        y: contourRoot.geometry.clampedRightPanelTopEdge - contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius
    }

    readonly property PathLine topAttachmentEdge: PathLine {
        x: contourRoot.geometry.rightPanelTopFullyMerged ? contourRoot.geometry.screenWidth : contourRoot.geometry.rightWindowBorderCenterX
        y: contourRoot.geometry.rightPanelTopFullyMerged ? 0 : contourRoot.geometry.clampedRightPanelTopEdge - contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius
    }

    readonly property PathLine topScreenCornerEdge: PathLine {
        x: contourRoot.geometry.rightPanelBorderLeftEdge - contourRoot.geometry.rightPanelCornerArcRadius
        y: 0
    }

    readonly property PathArc topJunctionArc: PathArc {
        x: contourRoot.geometry.rightPanelTopFullyMerged ? contourRoot.geometry.rightPanelBorderLeftEdge - contourRoot.geometry.rightPanelCornerArcRadius : contourRoot.geometry.rightWindowBorderCenterX - contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius
        y: contourRoot.geometry.clampedRightPanelTopEdge
        radiusX: contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius
        radiusY: contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius
        direction: PathArc.Clockwise
    }

    readonly property PathLine topCornerStart: PathLine {
        x: contourRoot.geometry.rightPanelBorderLeftEdge + (contourRoot.geometry.rightPanelTopFullyMerged ? -contourRoot.geometry.rightPanelCornerArcRadius : contourRoot.geometry.rightPanelCornerArcRadius)
        y: contourRoot.geometry.clampedRightPanelTopEdge
    }

    readonly property PathArc topCornerArc: PathArc {
        x: contourRoot.geometry.rightPanelBorderLeftEdge
        y: contourRoot.geometry.clampedRightPanelTopEdge + contourRoot.geometry.rightPanelCornerArcRadius
        radiusX: contourRoot.geometry.rightPanelCornerArcRadius
        radiusY: contourRoot.geometry.rightPanelCornerArcRadius
        direction: contourRoot.geometry.rightPanelTopFullyMerged ? PathArc.Clockwise : PathArc.Counterclockwise
    }

    readonly property PathLine leftEdge: PathLine {
        x: contourRoot.geometry.rightPanelBorderLeftEdge
        y: contourRoot.geometry.clampedRightPanelBottomEdge - contourRoot.geometry.rightPanelCornerArcRadius
    }

    readonly property PathArc bottomCornerArc: PathArc {
        x: contourRoot.geometry.rightPanelBorderLeftEdge + (contourRoot.geometry.rightPanelBottomFullyMerged ? -contourRoot.geometry.rightPanelCornerArcRadius : contourRoot.geometry.rightPanelCornerArcRadius)
        y: contourRoot.geometry.clampedRightPanelBottomEdge
        radiusX: contourRoot.geometry.rightPanelCornerArcRadius
        radiusY: contourRoot.geometry.rightPanelCornerArcRadius
        direction: contourRoot.geometry.rightPanelBottomFullyMerged ? PathArc.Clockwise : PathArc.Counterclockwise
    }

    readonly property PathLine bottomJunctionStart: PathLine {
        x: contourRoot.geometry.rightWindowBorderCenterX - contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius
        y: contourRoot.geometry.clampedRightPanelBottomEdge
    }

    readonly property PathArc bottomJunctionArc: PathArc {
        x: contourRoot.geometry.rightWindowBorderCenterX
        y: contourRoot.geometry.clampedRightPanelBottomEdge + contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius
        radiusX: contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius
        radiusY: contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius
        direction: PathArc.Clockwise
    }

    readonly property PathLine bottomScreenCornerEdge: PathLine {
        x: contourRoot.geometry.rightPanelBorderLeftEdge - contourRoot.geometry.rightPanelCornerArcRadius
        y: contourRoot.geometry.barHeight
    }

    readonly property PathLine bottomAttachmentEdge: PathLine {
        x: contourRoot.geometry.screenWidth
        y: contourRoot.geometry.rightPanelBottomFullyMerged ? contourRoot.geometry.barHeight : contourRoot.geometry.clampedRightPanelBottomEdge + contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius
    }

    readonly property list<QtObject> elements: [topAttachmentEdge, ...(geometry.rightPanelTopFullyMerged ? [topScreenCornerEdge] : [topJunctionArc]), topCornerStart, topCornerArc, leftEdge, bottomCornerArc, ...(geometry.rightPanelBottomFullyMerged ? [bottomScreenCornerEdge] : [bottomJunctionStart, bottomJunctionArc]), bottomAttachmentEdge]
    readonly property list<QtObject> borderElements: [borderStart, ...(geometry.rightPanelTopFullyMerged ? [] : [topJunctionArc, topCornerStart]), topCornerArc, leftEdge, bottomCornerArc, ...(geometry.rightPanelBottomFullyMerged ? [] : [bottomJunctionStart, bottomJunctionArc])]
}
