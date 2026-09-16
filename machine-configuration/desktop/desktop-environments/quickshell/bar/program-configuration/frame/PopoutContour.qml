import QtQuick

QtObject {
    id: contourRoot

    required property BarFrameGeometry geometry
    property list<QtObject> elements: [
        PathLine {
            x: contourRoot.geometry.bottomEdgeTargetX
            y: contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness
        },
        PathArc {
            x: contourRoot.geometry.bottomFullyMerged ? contourRoot.geometry.bottomEdgeTargetX : contourRoot.geometry.barWidth
            y: contourRoot.geometry.bottomFullyMerged ? contourRoot.geometry.clampedExtensionBottomEdge : (contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.effectiveBottomLeftBarCornerRadius)
            radiusX: contourRoot.geometry.effectiveBottomLeftBarCornerRadius
            radiusY: contourRoot.geometry.effectiveBottomLeftBarCornerRadius
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.bottomFullyMerged ? contourRoot.geometry.bottomEdgeTargetX : contourRoot.geometry.barWidth
            y: contourRoot.geometry.clampedExtensionBottomEdge + contourRoot.geometry.effectiveBottomJunctionArcRadius
        },
        PathArc {
            x: contourRoot.geometry.bottomFullyMerged ? contourRoot.geometry.bottomEdgeTargetX : (contourRoot.geometry.barWidth + contourRoot.geometry.effectiveBottomJunctionArcRadius)
            y: contourRoot.geometry.clampedExtensionBottomEdge
            radiusX: contourRoot.geometry.effectiveBottomJunctionArcRadius
            radiusY: contourRoot.geometry.effectiveBottomJunctionArcRadius
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.extensionRight - contourRoot.geometry.extensionCornerArcRadius
            y: contourRoot.geometry.clampedExtensionBottomEdge
        },
        PathArc {
            x: contourRoot.geometry.extensionRight
            y: contourRoot.geometry.clampedExtensionBottomEdge - contourRoot.geometry.extensionCornerArcRadius
            radiusX: contourRoot.geometry.extensionCornerArcRadius
            radiusY: contourRoot.geometry.extensionCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.extensionRight
            y: contourRoot.geometry.clampedExtensionTopEdge + contourRoot.geometry.extensionCornerArcRadius
        },
        PathArc {
            x: contourRoot.geometry.extensionRight - contourRoot.geometry.extensionCornerArcRadius
            y: contourRoot.geometry.clampedExtensionTopEdge
            radiusX: contourRoot.geometry.extensionCornerArcRadius
            radiusY: contourRoot.geometry.extensionCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.topFullyMerged ? contourRoot.geometry.topEdgeTargetX : (contourRoot.geometry.barWidth + contourRoot.geometry.effectiveTopJunctionArcRadius)
            y: contourRoot.geometry.clampedExtensionTopEdge
        },
        PathArc {
            x: contourRoot.geometry.topFullyMerged ? contourRoot.geometry.topEdgeTargetX : contourRoot.geometry.barWidth
            y: contourRoot.geometry.topFullyMerged ? contourRoot.geometry.clampedExtensionTopEdge : (contourRoot.geometry.clampedExtensionTopEdge - contourRoot.geometry.effectiveTopJunctionArcRadius)
            radiusX: contourRoot.geometry.effectiveTopJunctionArcRadius
            radiusY: contourRoot.geometry.effectiveTopJunctionArcRadius
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.topFullyMerged ? contourRoot.geometry.topEdgeTargetX : contourRoot.geometry.barWidth
            y: contourRoot.geometry.stripThickness + contourRoot.geometry.effectiveTopLeftBarCornerRadius
        },
        PathArc {
            x: contourRoot.geometry.topEdgeTargetX
            y: contourRoot.geometry.stripThickness
            radiusX: contourRoot.geometry.effectiveTopLeftBarCornerRadius
            radiusY: contourRoot.geometry.effectiveTopLeftBarCornerRadius
            direction: PathArc.Clockwise
        }
    ]
}
