import QtQuick

QtObject {
    id: contourRoot

    required property BarFrameGeometry geometry
    property list<QtObject> elements: [
        PathLine {
            x: contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightTopInnerCornerRadius
            y: contourRoot.geometry.stripThickness
        },
        PathArc {
            x: contourRoot.geometry.rightPanelTopFullyMerged ? (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightTopInnerCornerRadius) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.rightPanelTopFullyMerged ? contourRoot.geometry.clampedRightPanelTopEdge : (contourRoot.geometry.stripThickness + contourRoot.geometry.effectiveRightTopInnerCornerRadius)
            radiusX: contourRoot.geometry.effectiveRightTopInnerCornerRadius
            radiusY: contourRoot.geometry.effectiveRightTopInnerCornerRadius
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.rightPanelTopFullyMerged ? (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightTopInnerCornerRadius) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.hasRightPanel ? (contourRoot.geometry.clampedRightPanelTopEdge - contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius) : (contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius)
        },
        PathArc {
            x: contourRoot.geometry.hasRightPanel ? (contourRoot.geometry.rightPanelTopFullyMerged ? (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightTopInnerCornerRadius) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius)) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.clampedRightPanelTopEdge : (contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius)
            radiusX: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius : 0
            radiusY: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius : 0
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.hasRightPanel ? (contourRoot.geometry.rightPanelLeftEdge + contourRoot.geometry.rightPanelCornerArcRadius) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.clampedRightPanelTopEdge : (contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius)
        },
        PathArc {
            x: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.rightPanelLeftEdge : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.hasRightPanel ? (contourRoot.geometry.clampedRightPanelTopEdge + contourRoot.geometry.rightPanelCornerArcRadius) : (contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius)
            radiusX: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.rightPanelCornerArcRadius : 0
            radiusY: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.rightPanelCornerArcRadius : 0
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.rightPanelLeftEdge : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.hasRightPanel ? (contourRoot.geometry.clampedRightPanelBottomEdge - contourRoot.geometry.rightPanelCornerArcRadius) : (contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius)
        },
        PathArc {
            x: contourRoot.geometry.hasRightPanel ? (contourRoot.geometry.rightPanelLeftEdge + contourRoot.geometry.rightPanelCornerArcRadius) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.clampedRightPanelBottomEdge : (contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius)
            radiusX: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.rightPanelCornerArcRadius : 0
            radiusY: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.rightPanelCornerArcRadius : 0
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.hasRightPanel ? (contourRoot.geometry.rightPanelBottomFullyMerged ? (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius)) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.clampedRightPanelBottomEdge : (contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius)
        },
        PathArc {
            x: contourRoot.geometry.rightPanelBottomFullyMerged ? (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.hasRightPanel ? (contourRoot.geometry.clampedRightPanelBottomEdge + contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius) : (contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius)
            radiusX: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius : 0
            radiusY: contourRoot.geometry.hasRightPanel ? contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius : 0
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.rightPanelBottomFullyMerged ? (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius) : (contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness)
            y: contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius
        },
        PathArc {
            x: contourRoot.geometry.screenWidth - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveRightBottomInnerCornerRadius
            y: contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness
            radiusX: contourRoot.geometry.effectiveRightBottomInnerCornerRadius
            radiusY: contourRoot.geometry.effectiveRightBottomInnerCornerRadius
            direction: PathArc.Clockwise
        }
    ]
}
