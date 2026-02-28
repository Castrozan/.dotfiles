import QtQuick
import QtQuick.Shapes

ShapePath {
    id: shapePathRoot

    required property real barWidth
    required property real barHeight
    required property real screenWidth
    required property real junctionRadius
    required property real extensionY
    required property real extensionHeight
    required property real extensionWidth

    readonly property real stripThickness: barWidth / 3

    readonly property real innerCornerRadius: Math.min(junctionRadius, stripThickness)

    readonly property real barRightEdgeStartY: stripThickness + innerCornerRadius
    readonly property real barRightEdgeEndY: barHeight - stripThickness - innerCornerRadius

    readonly property real extensionTopEdge: extensionY
    readonly property real extensionBottomEdge: extensionY + extensionHeight

    readonly property bool hasExtension: extensionWidth > 0

    readonly property real topJunctionAvailableSpace: Math.max(0, extensionTopEdge - barRightEdgeStartY)
    readonly property real bottomJunctionAvailableSpace: Math.max(0, barRightEdgeEndY - extensionBottomEdge)

    readonly property real topJunctionArcRadius: Math.min(junctionRadius, extensionWidth, topJunctionAvailableSpace)
    readonly property real bottomJunctionArcRadius: Math.min(junctionRadius, extensionWidth, bottomJunctionAvailableSpace)

    readonly property real extensionCornerArcRadius: Math.min(junctionRadius, extensionWidth, extensionHeight / 2)
    readonly property real extensionRight: barWidth + extensionWidth

    fillColor: ThemeColors.background
    strokeWidth: -1

    startX: 0
    startY: 0

    PathLine {
        x: shapePathRoot.screenWidth
        y: 0
    }

    PathLine {
        x: shapePathRoot.screenWidth
        y: shapePathRoot.barHeight
    }

    PathLine {
        x: 0
        y: shapePathRoot.barHeight
    }

    PathLine {
        x: 0
        y: 0
    }

    PathMove {
        x: shapePathRoot.barWidth + shapePathRoot.innerCornerRadius
        y: shapePathRoot.stripThickness
    }

    PathLine {
        x: shapePathRoot.screenWidth - shapePathRoot.stripThickness - shapePathRoot.innerCornerRadius
        y: shapePathRoot.stripThickness
    }

    PathArc {
        x: shapePathRoot.screenWidth - shapePathRoot.stripThickness
        y: shapePathRoot.stripThickness + shapePathRoot.innerCornerRadius
        radiusX: shapePathRoot.innerCornerRadius
        radiusY: shapePathRoot.innerCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.screenWidth - shapePathRoot.stripThickness
        y: shapePathRoot.barHeight - shapePathRoot.stripThickness - shapePathRoot.innerCornerRadius
    }

    PathArc {
        x: shapePathRoot.screenWidth - shapePathRoot.stripThickness - shapePathRoot.innerCornerRadius
        y: shapePathRoot.barHeight - shapePathRoot.stripThickness
        radiusX: shapePathRoot.innerCornerRadius
        radiusY: shapePathRoot.innerCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.barWidth + shapePathRoot.innerCornerRadius
        y: shapePathRoot.barHeight - shapePathRoot.stripThickness
    }

    PathArc {
        x: shapePathRoot.barWidth
        y: shapePathRoot.barHeight - shapePathRoot.stripThickness - shapePathRoot.innerCornerRadius
        radiusX: shapePathRoot.innerCornerRadius
        radiusY: shapePathRoot.innerCornerRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.barWidth
        y: shapePathRoot.extensionBottomEdge + shapePathRoot.bottomJunctionArcRadius
    }

    PathArc {
        x: shapePathRoot.barWidth + shapePathRoot.bottomJunctionArcRadius
        y: shapePathRoot.extensionBottomEdge
        radiusX: shapePathRoot.bottomJunctionArcRadius
        radiusY: shapePathRoot.bottomJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.extensionRight - shapePathRoot.extensionCornerArcRadius
        y: shapePathRoot.extensionBottomEdge
    }

    PathArc {
        x: shapePathRoot.extensionRight
        y: shapePathRoot.extensionBottomEdge - shapePathRoot.extensionCornerArcRadius
        radiusX: shapePathRoot.extensionCornerArcRadius
        radiusY: shapePathRoot.extensionCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: shapePathRoot.extensionRight
        y: shapePathRoot.extensionTopEdge + shapePathRoot.extensionCornerArcRadius
    }

    PathArc {
        x: shapePathRoot.extensionRight - shapePathRoot.extensionCornerArcRadius
        y: shapePathRoot.extensionTopEdge
        radiusX: shapePathRoot.extensionCornerArcRadius
        radiusY: shapePathRoot.extensionCornerArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: shapePathRoot.barWidth + shapePathRoot.topJunctionArcRadius
        y: shapePathRoot.extensionTopEdge
    }

    PathArc {
        x: shapePathRoot.barWidth
        y: shapePathRoot.extensionTopEdge - shapePathRoot.topJunctionArcRadius
        radiusX: shapePathRoot.topJunctionArcRadius
        radiusY: shapePathRoot.topJunctionArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: shapePathRoot.barWidth
        y: shapePathRoot.stripThickness + shapePathRoot.innerCornerRadius
    }

    PathArc {
        x: shapePathRoot.barWidth + shapePathRoot.innerCornerRadius
        y: shapePathRoot.stripThickness
        radiusX: shapePathRoot.innerCornerRadius
        radiusY: shapePathRoot.innerCornerRadius
        direction: PathArc.Clockwise
    }
}
