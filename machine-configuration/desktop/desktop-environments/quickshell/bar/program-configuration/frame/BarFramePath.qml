import QtQuick
import QtQuick.Shapes

ShapePath {
    id: framePathRoot

    required property real barWidth
    required property real barHeight
    required property real screenWidth
    required property real junctionRadius
    required property real extensionY
    required property real extensionHeight
    required property real extensionWidth
    required property real dashboardX
    required property real dashboardWidth
    required property real dashboardHeight
    required property real launcherX
    required property real launcherWidth
    required property real launcherHeight
    required property real rightPanelY
    required property real rightPanelWidth
    required property real rightPanelHeight

    readonly property BarFrameGeometry geometry: BarFrameGeometry {
        barWidth: framePathRoot.barWidth
        barHeight: framePathRoot.barHeight
        screenWidth: framePathRoot.screenWidth
        junctionRadius: framePathRoot.junctionRadius
        extensionY: framePathRoot.extensionY
        extensionHeight: framePathRoot.extensionHeight
        extensionWidth: framePathRoot.extensionWidth
        dashboardX: framePathRoot.dashboardX
        dashboardWidth: framePathRoot.dashboardWidth
        dashboardHeight: framePathRoot.dashboardHeight
        launcherX: framePathRoot.launcherX
        launcherWidth: framePathRoot.launcherWidth
        launcherHeight: framePathRoot.launcherHeight
        rightPanelY: framePathRoot.rightPanelY
        rightPanelWidth: framePathRoot.rightPanelWidth
        rightPanelHeight: framePathRoot.rightPanelHeight
    }

    readonly property DashboardContour dashboardContour: DashboardContour {
        geometry: framePathRoot.geometry
    }

    readonly property RightPanelContour rightPanelContour: RightPanelContour {
        geometry: framePathRoot.geometry
    }

    readonly property LauncherContour launcherContour: LauncherContour {
        geometry: framePathRoot.geometry
    }

    readonly property PopoutContour popoutContour: PopoutContour {
        geometry: framePathRoot.geometry
    }

    startX: geometry.topEdgeTargetX
    startY: geometry.stripThickness
    pathElements: [...dashboardContour.elements, ...rightPanelContour.elements, ...launcherContour.elements, ...popoutContour.elements]
}
