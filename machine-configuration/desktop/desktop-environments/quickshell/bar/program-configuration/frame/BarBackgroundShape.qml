pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Shapes
import ".."

Shape {
    id: backgroundRoot

    required property BarFrameGeometry geometry
    property color fillColor: ThemeColors.backgroundSolid
    property color strokeColor: ThemeColors.accent

    preferredRendererType: Shape.CurveRenderer

    readonly property DashboardContour dashboardContour: DashboardContour {
        geometry: backgroundRoot.geometry
    }
    readonly property LauncherContour launcherContour: LauncherContour {
        geometry: backgroundRoot.geometry
    }
    readonly property RightPanelContour rightPanelContour: RightPanelContour {
        geometry: backgroundRoot.geometry
    }
    readonly property PopoutContour popoutContour: PopoutContour {
        geometry: backgroundRoot.geometry
    }

    component FilledPanelPath: ShapePath {
        fillColor: backgroundRoot.fillColor
        fillRule: ShapePath.WindingFill
        strokeColor: backgroundRoot.strokeColor
        strokeWidth: 2
        joinStyle: ShapePath.RoundJoin
        capStyle: ShapePath.RoundCap
    }

    component PanelOutline: QtObject {
        required property list<QtObject> elements
    }

    readonly property PanelOutline barOutline: PanelOutline {
        readonly property PathMove start: PathMove {
            x: 0
            y: 0
        }
        readonly property PathLine bottom: PathLine {
            x: 0
            y: backgroundRoot.geometry.barHeight
        }
        readonly property PathLine closure: PathLine {
            x: 0
            y: 0
        }
        elements: [start, bottom, ...backgroundRoot.popoutContour.elements, closure]
    }

    readonly property PanelOutline dashboardOutline: PanelOutline {
        readonly property PathMove start: PathMove {
            x: backgroundRoot.geometry.dashboardX - backgroundRoot.geometry.dashboardLeftJunctionArcRadius
            y: 0
        }
        elements: [start, ...backgroundRoot.dashboardContour.elements]
    }

    readonly property PanelOutline launcherOutline: PanelOutline {
        readonly property PathMove start: PathMove {
            x: backgroundRoot.geometry.launcherRightEdge + backgroundRoot.geometry.launcherRightJunctionArcRadius
            y: backgroundRoot.geometry.barHeight
        }
        elements: [start, ...backgroundRoot.launcherContour.elements]
    }

    readonly property PanelOutline rightPanelOutline: PanelOutline {
        readonly property PathMove start: PathMove {
            x: backgroundRoot.geometry.screenWidth
            y: backgroundRoot.geometry.clampedRightPanelTopEdge - backgroundRoot.geometry.effectiveRightPanelTopJunctionArcRadius
        }
        elements: [start, ...backgroundRoot.rightPanelContour.elements]
    }

    FilledPanelPath {
        strokeWidth: -1
        pathElements: backgroundRoot.geometry.leftBarWidth > 0 || backgroundRoot.geometry.hasExtension ? backgroundRoot.barOutline.elements : []
    }
    FilledPanelPath {
        fillColor: "transparent"
        startX: backgroundRoot.geometry.bottomEdgeTargetX
        startY: backgroundRoot.geometry.barHeight
        pathElements: backgroundRoot.geometry.leftBarWidth > 0 || backgroundRoot.geometry.hasExtension ? backgroundRoot.popoutContour.elements : []
    }
    FilledPanelPath {
        pathElements: backgroundRoot.geometry.hasDashboard ? backgroundRoot.dashboardOutline.elements : []
    }
    FilledPanelPath {
        pathElements: backgroundRoot.geometry.hasLauncher ? backgroundRoot.launcherOutline.elements : []
    }
    FilledPanelPath {
        pathElements: backgroundRoot.geometry.hasRightPanel ? backgroundRoot.rightPanelOutline.elements : []
    }
}
