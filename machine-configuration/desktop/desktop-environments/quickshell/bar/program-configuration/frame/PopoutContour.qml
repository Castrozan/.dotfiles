import QtQuick

QtObject {
    id: contourRoot

    required property BarFrameGeometry geometry
    readonly property list<QtObject> bottomCornerElements: [
        PathLine {
            x: contourRoot.geometry.bottomEdgeTargetX
            y: contourRoot.geometry.bottomWindowBorderCenterY
        },
        PathArc {
            x: contourRoot.geometry.bottomFullyMerged ? contourRoot.geometry.bottomEdgeTargetX : contourRoot.geometry.leftBarBorderRightEdge
            y: contourRoot.geometry.bottomFullyMerged ? contourRoot.geometry.clampedExtensionBottomEdge : (contourRoot.geometry.bottomWindowBorderCenterY - contourRoot.geometry.effectiveBottomLeftBarCornerRadius)
            radiusX: contourRoot.geometry.effectiveBottomLeftBarCornerRadius
            radiusY: contourRoot.geometry.effectiveBottomLeftBarCornerRadius
            direction: PathArc.Clockwise
        }
    ]

    readonly property list<QtObject> extensionElements: [
        PathLine {
            x: contourRoot.geometry.bottomFullyMerged ? contourRoot.geometry.bottomEdgeTargetX : contourRoot.geometry.leftBarBorderRightEdge
            y: contourRoot.geometry.clampedExtensionBottomEdge + contourRoot.geometry.effectiveBottomJunctionArcRadius
        },
        PathArc {
            x: contourRoot.geometry.bottomFullyMerged ? contourRoot.geometry.bottomEdgeTargetX : (contourRoot.geometry.leftBarBorderRightEdge + contourRoot.geometry.effectiveBottomJunctionArcRadius)
            y: contourRoot.geometry.clampedExtensionBottomEdge
            radiusX: contourRoot.geometry.effectiveBottomJunctionArcRadius
            radiusY: contourRoot.geometry.effectiveBottomJunctionArcRadius
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.bottomFullyMerged ? contourRoot.geometry.bottomEdgeTargetX : contourRoot.geometry.extensionBorderRightEdge - contourRoot.geometry.extensionCornerArcRadius
            y: contourRoot.geometry.clampedExtensionBottomEdge
        },
        PathArc {
            x: contourRoot.geometry.extensionBorderRightEdge
            y: contourRoot.geometry.clampedExtensionBottomEdge - contourRoot.geometry.extensionCornerArcRadius
            radiusX: contourRoot.geometry.extensionCornerArcRadius
            radiusY: contourRoot.geometry.extensionCornerArcRadius
            direction: contourRoot.geometry.bottomFullyMerged ? PathArc.Clockwise : PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.extensionBorderRightEdge
            y: contourRoot.geometry.clampedExtensionTopEdge + contourRoot.geometry.extensionCornerArcRadius
        },
        PathArc {
            x: contourRoot.geometry.topFullyMerged ? contourRoot.geometry.topEdgeTargetX : contourRoot.geometry.extensionBorderRightEdge - contourRoot.geometry.extensionCornerArcRadius
            y: contourRoot.geometry.clampedExtensionTopEdge
            radiusX: contourRoot.geometry.extensionCornerArcRadius
            radiusY: contourRoot.geometry.extensionCornerArcRadius
            direction: contourRoot.geometry.topFullyMerged ? PathArc.Clockwise : PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.topFullyMerged ? contourRoot.geometry.topEdgeTargetX : (contourRoot.geometry.leftBarBorderRightEdge + contourRoot.geometry.effectiveTopJunctionArcRadius)
            y: contourRoot.geometry.clampedExtensionTopEdge
        },
        PathArc {
            x: contourRoot.geometry.topFullyMerged ? contourRoot.geometry.topEdgeTargetX : contourRoot.geometry.leftBarBorderRightEdge
            y: contourRoot.geometry.topFullyMerged ? contourRoot.geometry.clampedExtensionTopEdge : (contourRoot.geometry.clampedExtensionTopEdge - contourRoot.geometry.effectiveTopJunctionArcRadius)
            radiusX: contourRoot.geometry.effectiveTopJunctionArcRadius
            radiusY: contourRoot.geometry.effectiveTopJunctionArcRadius
            direction: PathArc.Clockwise
        }
    ]

    readonly property list<QtObject> topCornerElements: [
        PathLine {
            x: contourRoot.geometry.topFullyMerged ? contourRoot.geometry.topEdgeTargetX : contourRoot.geometry.leftBarBorderRightEdge
            y: contourRoot.geometry.topWindowBorderCenterY + contourRoot.geometry.effectiveTopLeftBarCornerRadius
        },
        PathArc {
            x: contourRoot.geometry.topEdgeTargetX
            y: contourRoot.geometry.topWindowBorderCenterY
            radiusX: contourRoot.geometry.effectiveTopLeftBarCornerRadius
            radiusY: contourRoot.geometry.effectiveTopLeftBarCornerRadius
            direction: PathArc.Clockwise
        }
    ]

    readonly property list<QtObject> elements: geometry.hasExtension ? [...bottomCornerElements, ...extensionElements, ...topCornerElements] : [...bottomCornerElements, ...topCornerElements]
}
