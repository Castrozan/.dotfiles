pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Shapes
import ".."

Shape {
    id: backgroundRoot

    required property BarFrameGeometry geometry
    property color fillColor: ThemeColors.backgroundSolid
    property color strokeColor: ThemeColors.accent
    property bool desktopBorderVisible: false

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
        strokeWidth: backgroundRoot.geometry.windowBorderWidth
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
        readonly property PathLine bottomAttachmentEdge: PathLine {
            x: backgroundRoot.geometry.bottomEdgeTargetX
            y: backgroundRoot.geometry.barHeight
        }
        readonly property PathLine topAttachmentEdge: PathLine {
            x: backgroundRoot.geometry.topEdgeTargetX
            y: 0
        }
        readonly property PathLine closure: PathLine {
            x: 0
            y: 0
        }
        elements: [start, bottom, bottomAttachmentEdge, ...backgroundRoot.popoutContour.elements, topAttachmentEdge, closure]
    }

    readonly property PanelOutline dashboardOutline: PanelOutline {
        readonly property PathMove start: PathMove {
            x: backgroundRoot.geometry.dashboardBorderLeftEdge - backgroundRoot.geometry.dashboardLeftJunctionArcRadius
            y: backgroundRoot.geometry.topWindowBorderCenterY
        }
        elements: [start, ...backgroundRoot.dashboardContour.elements]
    }

    readonly property PanelOutline launcherOutline: PanelOutline {
        readonly property PathMove start: PathMove {
            x: backgroundRoot.geometry.launcherBorderRightEdge + backgroundRoot.geometry.launcherRightJunctionArcRadius
            y: backgroundRoot.geometry.bottomWindowBorderCenterY
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

    readonly property PathRectangle dashboardAttachmentCover: PathRectangle {
        x: backgroundRoot.geometry.dashboardBorderLeftEdge - backgroundRoot.geometry.dashboardLeftJunctionArcRadius
        y: 0
        width: backgroundRoot.geometry.dashboardBorderRightEdge + backgroundRoot.geometry.dashboardRightJunctionArcRadius - x
        height: backgroundRoot.geometry.topWindowBorderCenterY
    }
    readonly property PathRectangle launcherAttachmentCover: PathRectangle {
        x: backgroundRoot.geometry.launcherBorderLeftEdge - backgroundRoot.geometry.launcherLeftJunctionArcRadius
        y: backgroundRoot.geometry.bottomWindowBorderCenterY
        width: backgroundRoot.geometry.launcherBorderRightEdge + backgroundRoot.geometry.launcherRightJunctionArcRadius - x
        height: backgroundRoot.geometry.barHeight - y
    }

    readonly property PathRectangle desktopBorder: PathRectangle {
        x: backgroundRoot.geometry.windowBorderInset
        y: backgroundRoot.geometry.topWindowBorderCenterY
        width: backgroundRoot.geometry.screenWidth - backgroundRoot.geometry.windowBorderWidth
        height: backgroundRoot.geometry.barHeight - backgroundRoot.geometry.windowBorderWidth
        radius: backgroundRoot.geometry.windowCornerRadius
    }

    FilledPanelPath {
        fillColor: "transparent"
        pathElements: backgroundRoot.desktopBorderVisible ? [backgroundRoot.desktopBorder] : []
    }
    FilledPanelPath {
        strokeWidth: -1
        pathElements: backgroundRoot.geometry.leftBarWidth > 0 || backgroundRoot.geometry.hasExtension ? backgroundRoot.barOutline.elements : []
    }
    FilledPanelPath {
        fillColor: "transparent"
        startX: backgroundRoot.geometry.bottomEdgeTargetX
        startY: backgroundRoot.geometry.bottomWindowBorderCenterY
        pathElements: backgroundRoot.geometry.leftBarWidth > 0 || backgroundRoot.geometry.hasExtension ? backgroundRoot.popoutContour.elements : []
    }
    FilledPanelPath {
        strokeWidth: -1
        pathElements: backgroundRoot.geometry.hasDashboard ? [backgroundRoot.dashboardAttachmentCover] : []
    }
    FilledPanelPath {
        pathElements: backgroundRoot.geometry.hasDashboard ? backgroundRoot.dashboardOutline.elements : []
    }
    FilledPanelPath {
        strokeWidth: -1
        pathElements: backgroundRoot.geometry.hasLauncher ? [backgroundRoot.launcherAttachmentCover] : []
    }
    FilledPanelPath {
        pathElements: backgroundRoot.geometry.hasLauncher ? backgroundRoot.launcherOutline.elements : []
    }
    FilledPanelPath {
        strokeWidth: -1
        pathElements: backgroundRoot.geometry.hasRightPanel ? backgroundRoot.rightPanelOutline.elements : []
    }
    FilledPanelPath {
        fillColor: "transparent"
        pathElements: backgroundRoot.geometry.hasRightPanel ? backgroundRoot.rightPanelContour.borderElements : []
    }
}
