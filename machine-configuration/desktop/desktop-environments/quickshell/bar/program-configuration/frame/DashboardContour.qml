import QtQuick

QtObject {
    id: contourRoot

    required property BarFrameGeometry geometry
    property list<QtObject> elements: [
        PathLine {
            x: contourRoot.geometry.dashboardBorderLeftEdge - contourRoot.geometry.dashboardLeftJunctionArcRadius
            y: contourRoot.geometry.topWindowBorderCenterY
        },
        PathArc {
            x: contourRoot.geometry.dashboardBorderLeftEdge
            y: contourRoot.geometry.topWindowBorderCenterY + contourRoot.geometry.dashboardLeftJunctionArcRadius
            radiusX: contourRoot.geometry.dashboardLeftJunctionArcRadius
            radiusY: contourRoot.geometry.dashboardLeftJunctionArcRadius
            direction: PathArc.Clockwise
        },
        PathLine {
            x: contourRoot.geometry.dashboardBorderLeftEdge
            y: contourRoot.geometry.dashboardBorderBottomEdge - contourRoot.geometry.dashboardCornerArcRadius
        },
        PathArc {
            x: contourRoot.geometry.dashboardBorderLeftEdge + contourRoot.geometry.dashboardCornerArcRadius
            y: contourRoot.geometry.dashboardBorderBottomEdge
            radiusX: contourRoot.geometry.dashboardCornerArcRadius
            radiusY: contourRoot.geometry.dashboardCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.dashboardBorderRightEdge - contourRoot.geometry.dashboardCornerArcRadius
            y: contourRoot.geometry.dashboardBorderBottomEdge
        },
        PathArc {
            x: contourRoot.geometry.dashboardBorderRightEdge
            y: contourRoot.geometry.dashboardBorderBottomEdge - contourRoot.geometry.dashboardCornerArcRadius
            radiusX: contourRoot.geometry.dashboardCornerArcRadius
            radiusY: contourRoot.geometry.dashboardCornerArcRadius
            direction: PathArc.Counterclockwise
        },
        PathLine {
            x: contourRoot.geometry.dashboardBorderRightEdge
            y: contourRoot.geometry.topWindowBorderCenterY + contourRoot.geometry.dashboardRightJunctionArcRadius
        },
        PathArc {
            x: contourRoot.geometry.dashboardBorderRightEdge + contourRoot.geometry.dashboardRightJunctionArcRadius
            y: contourRoot.geometry.topWindowBorderCenterY
            radiusX: contourRoot.geometry.dashboardRightJunctionArcRadius
            radiusY: contourRoot.geometry.dashboardRightJunctionArcRadius
            direction: PathArc.Clockwise
        }
    ]
}
