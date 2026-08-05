import QtQuick
import QtQuick.Shapes
import ".."

ShapePath {
    id: popoutBorderShapeRoot

    required property real barWidth
    required property real barHeight
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

    fillColor: "transparent"
    strokeColor: ThemeColors.accent
    strokeWidth: hasExtension ? 1 : -1
    joinStyle: ShapePath.RoundJoin
    capStyle: ShapePath.RoundCap

    startX: barWidth
    startY: extensionTopEdge - topJunctionArcRadius

    PathArc {
        x: popoutBorderShapeRoot.barWidth + popoutBorderShapeRoot.topJunctionArcRadius
        y: popoutBorderShapeRoot.extensionTopEdge
        radiusX: popoutBorderShapeRoot.topJunctionArcRadius
        radiusY: popoutBorderShapeRoot.topJunctionArcRadius
        direction: PathArc.Counterclockwise
    }

    PathLine {
        x: popoutBorderShapeRoot.extensionRight - popoutBorderShapeRoot.extensionCornerArcRadius
        y: popoutBorderShapeRoot.extensionTopEdge
    }

    PathArc {
        x: popoutBorderShapeRoot.extensionRight
        y: popoutBorderShapeRoot.extensionTopEdge + popoutBorderShapeRoot.extensionCornerArcRadius
        radiusX: popoutBorderShapeRoot.extensionCornerArcRadius
        radiusY: popoutBorderShapeRoot.extensionCornerArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: popoutBorderShapeRoot.extensionRight
        y: popoutBorderShapeRoot.extensionBottomEdge - popoutBorderShapeRoot.extensionCornerArcRadius
    }

    PathArc {
        x: popoutBorderShapeRoot.extensionRight - popoutBorderShapeRoot.extensionCornerArcRadius
        y: popoutBorderShapeRoot.extensionBottomEdge
        radiusX: popoutBorderShapeRoot.extensionCornerArcRadius
        radiusY: popoutBorderShapeRoot.extensionCornerArcRadius
        direction: PathArc.Clockwise
    }

    PathLine {
        x: popoutBorderShapeRoot.barWidth + popoutBorderShapeRoot.bottomJunctionArcRadius
        y: popoutBorderShapeRoot.extensionBottomEdge
    }

    PathArc {
        x: popoutBorderShapeRoot.barWidth
        y: popoutBorderShapeRoot.extensionBottomEdge + popoutBorderShapeRoot.bottomJunctionArcRadius
        radiusX: popoutBorderShapeRoot.bottomJunctionArcRadius
        radiusY: popoutBorderShapeRoot.bottomJunctionArcRadius
        direction: PathArc.Counterclockwise
    }
}
