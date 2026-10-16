import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import QtQuick
import ".."
import "../panels"

Scope {
    id: screenScope

    required property var screen
    required property QtObject shellEvents

    readonly property int barContentWidth: 48
    readonly property int barTotalWidth: barContentWidth

    readonly property var workspaceMonitor: Hyprland.monitorFor(screen)

    VisibleWorkspaceWindows {
        id: visibleWorkspaceWindows
        monitorId: screenScope.workspaceMonitor ? screenScope.workspaceMonitor.id : -1
        workspaceId: screenScope.workspaceMonitor?.activeWorkspace?.id ?? 0
        specialWorkspaceId: screenScope.workspaceMonitor?.lastIpcObject?.specialWorkspace?.id ?? 0
    }

    Process {
        id: workspaceWindowsQueryProcess
        command: ["hyprctl", "clients", "-j"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    visibleWorkspaceWindows.clients = JSON.parse(data);
                } catch (e) {
                    visibleWorkspaceWindows.clients = null;
                }
            }
        }
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0)
                visibleWorkspaceWindows.clients = null;
        }
    }

    Component.onCompleted: workspaceWindowsQueryProcess.running = true

    Connections {
        target: screenScope.workspaceMonitor
        function onActiveWorkspaceChanged() {
            workspaceWindowsQueryProcess.running = true;
        }
    }

    Connections {
        target: screenScope.shellEvents
        function onHyprlandFullscreenEventReceived() {
            workspaceWindowsQueryProcess.running = true;
        }
        function onHyprlandWindowLayoutEventReceived() {
            workspaceWindowsQueryProcess.running = true;
        }
    }
    readonly property int shapeJunctionRadius: 36

    QtObject {
        id: popoutIconAnchors

        function centerYForPopout(name: string): real {
            let iconPosition = drawersWindow.barItem.statusIconPositions[name];
            if (!iconPosition)
                return drawersWindow.height / 2;
            let sceneTop = drawersWindow.barItem.mapToItem(null, 0, iconPosition.top).y;
            let sceneBottom = drawersWindow.barItem.mapToItem(null, 0, iconPosition.bottom).y;
            return (sceneTop + sceneBottom) / 2;
        }
    }

    DrawerState {
        id: screenDrawerState

        popoutAnchorResolver: popoutIconAnchors
        popoutIconHovered: drawersWindow.barItem.hasHoveredPopoutIcon
    }

    DrawerHoverController {
        id: screenHoverController

        drawerState: screenDrawerState
        activeWorkspaceId: visibleWorkspaceWindows.workspaceId
        pointerOverBar: drawersWindow.pointerOverBar
    }

    DrawerIpcAdapter {
        drawerState: screenDrawerState
        drawerHoverController: screenHoverController
    }

    Connections {
        target: screenScope.shellEvents
        function onOsdSocketMessageReceived(message: string): void {
            drawersWindow.handleOsdMessage(message);
        }
    }

    ScreenDrawerWindow {
        id: drawersWindow
        screen: screenScope.screen
        barTotalWidth: screenScope.barTotalWidth
        shapeJunctionRadius: screenScope.shapeJunctionRadius
        activeWorkspaceHasFullscreenWindow: visibleWorkspaceWindows.hasFullscreenWindow
        activeWorkspaceIsEmpty: visibleWorkspaceWindows.isEmpty
        drawerState: screenDrawerState
        hoverController: screenHoverController
    }

    WallpaperTransitionOverlay {
        screen: screenScope.screen
    }
}
