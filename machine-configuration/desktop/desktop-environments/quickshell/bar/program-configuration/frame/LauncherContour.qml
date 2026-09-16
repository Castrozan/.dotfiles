import QtQuick

QtObject {
    id: contourRoot

    required property BarFrameGeometry geometry
    property list<QtObject> elements: [
        PathLine {
            x: contourRoot.geometry.launcherRightEdge + contourRoot.geometry.launcherRightJunctionArcRadius
            y: contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness
        },
        PathArc {
            x: contourRoot.geometry.launcherRightEdge
            y: contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.launcherRightJunctionArcRadius
            radiusX: contourRoot.geometry.launcherRightJunctionArcRadius
            radiusY: contourRoot.geometry.launcherRightJunctionArcRadius
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.launcherRightEdge
            y: contourRoot.geometry.launcherTopEdge + contourRoot.geometry.launcherCornerArcRadius
        },
        PathArc {
            x: contourRoot.geometry.launcherRightEdge - contourRoot.geometry.launcherCornerArcRadius
            y: contourRoot.geometry.launcherTopEdge
            radiusX: contourRoot.geometry.launcherCornerArcRadius
            radiusY: contourRoot.geometry.launcherCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.launcherX + contourRoot.geometry.launcherCornerArcRadius
            y: contourRoot.geometry.launcherTopEdge
        },
        PathArc {
            x: contourRoot.geometry.launcherX
            y: contourRoot.geometry.launcherTopEdge + contourRoot.geometry.launcherCornerArcRadius
            radiusX: contourRoot.geometry.launcherCornerArcRadius
            radiusY: contourRoot.geometry.launcherCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.launcherX
            y: contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness - contourRoot.geometry.launcherLeftJunctionArcRadius
        },
        PathArc {
            x: contourRoot.geometry.launcherX - contourRoot.geometry.launcherLeftJunctionArcRadius
            y: contourRoot.geometry.barHeight - contourRoot.geometry.stripThickness
            radiusX: contourRoot.geometry.launcherLeftJunctionArcRadius
            radiusY: contourRoot.geometry.launcherLeftJunctionArcRadius
            direction: PathArc.Clockwise
        }
    ]
}
