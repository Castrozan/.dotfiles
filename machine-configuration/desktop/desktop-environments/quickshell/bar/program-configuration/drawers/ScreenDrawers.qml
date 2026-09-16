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

    property bool activeWorkspaceHasFullscreenWindow: false

    Process {
        id: activeWorkspaceFullscreenQueryProcess
        command: ["hyprctl", "clients", "-j"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                try {
                    let clients = JSON.parse(data);
                    let wsId = Hyprland.focusedWorkspace ? Hyprland.focusedWorkspace.id : -1;
                    screenScope.activeWorkspaceHasFullscreenWindow = clients.some(c => c.workspace.id === wsId && c.fullscreen === 2);
                } catch (e) {
                    screenScope.activeWorkspaceHasFullscreenWindow = false;
                }
            }
        }
    }

    Component.onCompleted: activeWorkspaceFullscreenQueryProcess.running = true

    Connections {
        target: Hyprland
        function onFocusedWorkspaceChanged() {
            activeWorkspaceFullscreenQueryProcess.running = true;
        }
    }

    Connections {
        target: screenScope.shellEvents
        function onHyprlandFullscreenEventReceived() {
            activeWorkspaceFullscreenQueryProcess.running = true;
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
        activeWorkspaceHasFullscreenWindow: screenScope.activeWorkspaceHasFullscreenWindow
        drawerState: screenDrawerState
        hoverController: screenHoverController
    }

    WallpaperTransitionOverlay {
        screen: screenScope.screen
    }

    ExclusionZones {
        screen: screenScope.screen
        barWidth: barTotalWidth
    }
}
