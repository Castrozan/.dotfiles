import QtQuick
import QtQuick.Shapes
import ".."

BarFramePath {
    id: backgroundRoot

    readonly property real cutoutPathStartPointOffset: 3
    readonly property QtObject outerRectangle: QtObject {
        property list<QtObject> elements: [
            PathLine {
                x: backgroundRoot.geometry.screenWidth
                y: 0
            },
            PathLine {
                x: backgroundRoot.geometry.screenWidth
                y: backgroundRoot.geometry.barHeight
            },
            PathLine {
                x: 0
                y: backgroundRoot.geometry.barHeight
            },
            PathLine {
                x: 0
                y: 0
            },
            PathMove {
                x: backgroundRoot.geometry.topEdgeTargetX + backgroundRoot.cutoutPathStartPointOffset
                y: backgroundRoot.geometry.stripThickness
            }
        ]
    }

    readonly property PathLine cutoutClosure: PathLine {
        x: backgroundRoot.geometry.topEdgeTargetX + backgroundRoot.cutoutPathStartPointOffset
        y: backgroundRoot.geometry.stripThickness
    }

    fillColor: ThemeColors.background
    strokeWidth: -1
    startX: 0
    startY: 0
    pathElements: [...outerRectangle.elements, ...dashboardContour.elements, ...rightPanelContour.elements, ...launcherContour.elements, ...popoutContour.elements, cutoutClosure]
}
