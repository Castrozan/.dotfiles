pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Shapes
import ".."

Shape {
    id: backgroundRoot

    required property BarFrameGeometry geometry
    property color fillColor: ThemeColors.background
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

    component ClosedPanelOutline: QtObject {
        required property list<QtObject> elements
    }

    readonly property ClosedPanelOutline barOutline: ClosedPanelOutline {
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

    readonly property ClosedPanelOutline dashboardOutline: ClosedPanelOutline {
        id: dashboardOutlineRoot
        readonly property PathMove start: PathMove {
            x: backgroundRoot.geometry.dashboardX - backgroundRoot.geometry.dashboardLeftJunctionArcRadius
            y: 0
        }
        readonly property PathLine closure: PathLine {
            x: dashboardOutlineRoot.start.x
            y: dashboardOutlineRoot.start.y
        }
        elements: [start, ...backgroundRoot.dashboardContour.elements, closure]
    }

    readonly property ClosedPanelOutline launcherOutline: ClosedPanelOutline {
        id: launcherOutlineRoot
        readonly property PathMove start: PathMove {
            x: backgroundRoot.geometry.launcherRightEdge + backgroundRoot.geometry.launcherRightJunctionArcRadius
            y: backgroundRoot.geometry.barHeight
        }
        readonly property PathLine closure: PathLine {
            x: launcherOutlineRoot.start.x
            y: launcherOutlineRoot.start.y
        }
        elements: [start, ...backgroundRoot.launcherContour.elements, closure]
    }

    readonly property ClosedPanelOutline rightPanelOutline: ClosedPanelOutline {
        id: rightPanelOutlineRoot
        readonly property PathMove start: PathMove {
            x: backgroundRoot.geometry.screenWidth
            y: backgroundRoot.geometry.clampedRightPanelTopEdge - backgroundRoot.geometry.effectiveRightPanelTopJunctionArcRadius
        }
        readonly property PathLine closure: PathLine {
            x: rightPanelOutlineRoot.start.x
            y: rightPanelOutlineRoot.start.y
        }
        elements: [start, ...backgroundRoot.rightPanelContour.elements, closure]
    }

    FilledPanelPath {
        pathElements: backgroundRoot.geometry.leftBarWidth > 0 || backgroundRoot.geometry.hasExtension ? backgroundRoot.barOutline.elements : []
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
