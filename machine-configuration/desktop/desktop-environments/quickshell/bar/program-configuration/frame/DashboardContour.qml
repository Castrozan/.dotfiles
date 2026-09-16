import QtQuick

QtObject {
    id: contourRoot

    required property BarFrameGeometry geometry
    property list<QtObject> elements: [
        PathLine {
            x: contourRoot.geometry.dashboardX - contourRoot.geometry.dashboardLeftJunctionArcRadius
            y: contourRoot.geometry.stripThickness
        },
        PathArc {
            x: contourRoot.geometry.dashboardX
            y: contourRoot.geometry.stripThickness + contourRoot.geometry.dashboardLeftJunctionArcRadius
            radiusX: contourRoot.geometry.dashboardLeftJunctionArcRadius
            radiusY: contourRoot.geometry.dashboardLeftJunctionArcRadius
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.dashboardX
            y: contourRoot.geometry.dashboardBottomEdge - contourRoot.geometry.dashboardCornerArcRadius
        },
        PathArc {
            x: contourRoot.geometry.dashboardX + contourRoot.geometry.dashboardCornerArcRadius
            y: contourRoot.geometry.dashboardBottomEdge
            radiusX: contourRoot.geometry.dashboardCornerArcRadius
            radiusY: contourRoot.geometry.dashboardCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.dashboardRightEdge - contourRoot.geometry.dashboardCornerArcRadius
            y: contourRoot.geometry.dashboardBottomEdge
        },
        PathArc {
            x: contourRoot.geometry.dashboardRightEdge
            y: contourRoot.geometry.dashboardBottomEdge - contourRoot.geometry.dashboardCornerArcRadius
            radiusX: contourRoot.geometry.dashboardCornerArcRadius
            radiusY: contourRoot.geometry.dashboardCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.dashboardRightEdge
            y: contourRoot.geometry.stripThickness + contourRoot.geometry.dashboardRightJunctionArcRadius
        },
        PathArc {
            x: contourRoot.geometry.dashboardRightEdge + contourRoot.geometry.dashboardRightJunctionArcRadius
            y: contourRoot.geometry.stripThickness
            radiusX: contourRoot.geometry.dashboardRightJunctionArcRadius
            radiusY: contourRoot.geometry.dashboardRightJunctionArcRadius
            direction: PathArc.Clockwise
        }
    ]
}
