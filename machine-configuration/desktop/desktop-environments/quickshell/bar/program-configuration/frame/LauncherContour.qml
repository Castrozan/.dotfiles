import QtQuick

QtObject {
    id: contourRoot

    required property BarFrameGeometry geometry
    property list<QtObject> elements: [
        PathLine {
            x: contourRoot.geometry.launcherBorderRightEdge + contourRoot.geometry.launcherRightJunctionArcRadius
            y: contourRoot.geometry.bottomWindowBorderCenterY
        },
        PathArc {
            x: contourRoot.geometry.launcherBorderRightEdge
            y: contourRoot.geometry.bottomWindowBorderCenterY - contourRoot.geometry.launcherRightJunctionArcRadius
            radiusX: contourRoot.geometry.launcherRightJunctionArcRadius
            radiusY: contourRoot.geometry.launcherRightJunctionArcRadius
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.launcherBorderRightEdge
            y: contourRoot.geometry.launcherBorderTopEdge + contourRoot.geometry.launcherCornerArcRadius
        },
        PathArc {
            x: contourRoot.geometry.launcherBorderRightEdge - contourRoot.geometry.launcherCornerArcRadius
            y: contourRoot.geometry.launcherBorderTopEdge
            radiusX: contourRoot.geometry.launcherCornerArcRadius
            radiusY: contourRoot.geometry.launcherCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.launcherBorderLeftEdge + contourRoot.geometry.launcherCornerArcRadius
            y: contourRoot.geometry.launcherBorderTopEdge
        },
        PathArc {
            x: contourRoot.geometry.launcherBorderLeftEdge
            y: contourRoot.geometry.launcherBorderTopEdge + contourRoot.geometry.launcherCornerArcRadius
            radiusX: contourRoot.geometry.launcherCornerArcRadius
            radiusY: contourRoot.geometry.launcherCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.launcherBorderLeftEdge
            y: contourRoot.geometry.bottomWindowBorderCenterY - contourRoot.geometry.launcherLeftJunctionArcRadius
        },
        PathArc {
            x: contourRoot.geometry.launcherBorderLeftEdge - contourRoot.geometry.launcherLeftJunctionArcRadius
            y: contourRoot.geometry.bottomWindowBorderCenterY
            radiusX: contourRoot.geometry.launcherLeftJunctionArcRadius
            radiusY: contourRoot.geometry.launcherLeftJunctionArcRadius
            direction: PathArc.Clockwise
        }
    ]
}
