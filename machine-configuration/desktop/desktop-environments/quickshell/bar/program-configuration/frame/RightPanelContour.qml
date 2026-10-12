import QtQuick

QtObject {
    id: contourRoot

    required property BarFrameGeometry geometry

    readonly property PathMove borderStart: PathMove {
        x: contourRoot.geometry.rightPanelTopFullyMerged ? contourRoot.geometry.rightPanelLeftEdge - contourRoot.geometry.rightPanelCornerArcRadius : contourRoot.geometry.screenWidth
        y: contourRoot.geometry.clampedRightPanelTopEdge - contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius
    }

    readonly property PathArc topJunctionArc: PathArc {
        x: contourRoot.geometry.rightPanelTopFullyMerged ? contourRoot.geometry.rightPanelLeftEdge - contourRoot.geometry.rightPanelCornerArcRadius : contourRoot.geometry.rightStripLeftEdge - contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius
        y: contourRoot.geometry.clampedRightPanelTopEdge
        radiusX: contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius
        radiusY: contourRoot.geometry.effectiveRightPanelTopJunctionArcRadius
        direction: PathArc.Clockwise
    }

    readonly property PathLine topCornerStart: PathLine {
        x: contourRoot.geometry.rightPanelLeftEdge + (contourRoot.geometry.rightPanelTopFullyMerged ? -contourRoot.geometry.rightPanelCornerArcRadius : contourRoot.geometry.rightPanelCornerArcRadius)
        y: contourRoot.geometry.clampedRightPanelTopEdge
    }

    readonly property PathArc topCornerArc: PathArc {
        x: contourRoot.geometry.rightPanelLeftEdge
        y: contourRoot.geometry.clampedRightPanelTopEdge + contourRoot.geometry.rightPanelCornerArcRadius
        radiusX: contourRoot.geometry.rightPanelCornerArcRadius
        radiusY: contourRoot.geometry.rightPanelCornerArcRadius
        direction: contourRoot.geometry.rightPanelTopFullyMerged ? PathArc.Clockwise : PathArc.Counterclockwise
    }

    readonly property PathLine leftEdge: PathLine {
        x: contourRoot.geometry.rightPanelLeftEdge
        y: contourRoot.geometry.clampedRightPanelBottomEdge - contourRoot.geometry.rightPanelCornerArcRadius
    }

    readonly property PathArc bottomCornerArc: PathArc {
        x: contourRoot.geometry.rightPanelLeftEdge + (contourRoot.geometry.rightPanelBottomFullyMerged ? -contourRoot.geometry.rightPanelCornerArcRadius : contourRoot.geometry.rightPanelCornerArcRadius)
        y: contourRoot.geometry.clampedRightPanelBottomEdge
        radiusX: contourRoot.geometry.rightPanelCornerArcRadius
        radiusY: contourRoot.geometry.rightPanelCornerArcRadius
        direction: contourRoot.geometry.rightPanelBottomFullyMerged ? PathArc.Clockwise : PathArc.Counterclockwise
    }

    readonly property PathLine bottomJunctionStart: PathLine {
        x: contourRoot.geometry.rightPanelBottomFullyMerged ? contourRoot.geometry.rightStripLeftEdge : contourRoot.geometry.rightStripLeftEdge - contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius
        y: contourRoot.geometry.clampedRightPanelBottomEdge
    }

    readonly property PathArc bottomJunctionArc: PathArc {
        x: contourRoot.geometry.rightStripLeftEdge
        y: contourRoot.geometry.clampedRightPanelBottomEdge + contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius
        radiusX: contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius
        radiusY: contourRoot.geometry.effectiveRightPanelBottomJunctionArcRadius
        direction: PathArc.Clockwise
    }

    readonly property list<QtObject> elements: [topJunctionArc, topCornerStart, topCornerArc, leftEdge, bottomCornerArc, bottomJunctionStart, bottomJunctionArc]
    readonly property list<QtObject> borderElements: [borderStart, ...(geometry.rightPanelTopFullyMerged ? [] : [topJunctionArc, topCornerStart]), topCornerArc, leftEdge, bottomCornerArc, ...(geometry.rightPanelBottomFullyMerged ? [] : [bottomJunctionStart, bottomJunctionArc])]
}
