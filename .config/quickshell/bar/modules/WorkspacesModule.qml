import Quickshell.Hyprland
import QtQuick
import QtQuick.Layouts
import ".."

ColumnLayout {
    id: workspacesModuleRoot

    readonly property int slotsPerPage: 7
    readonly property int focusedWorkspaceId: Hyprland.focusedWorkspace ? Hyprland.focusedWorkspace.id : 1
    readonly property int currentPageStart: Math.floor((focusedWorkspaceId - 1) / slotsPerPage) * slotsPerPage + 1
    readonly property int warningSlotIndex: 3
    property var occupiedWorkspaceIds: ({})

    function _refreshOccupiedWorkspaces(): void {
        Hyprland.refreshWorkspaces();
        let occupied = {};
        let workspaces = Hyprland.workspaces.values;
        for (let i = 0; i < workspaces.length; i++) {
            let ws = workspaces[i];
            let windowCount = ws.lastIpcObject ? ws.lastIpcObject.windows : 0;
            if (windowCount > 0) {
                occupied[ws.id] = true;
            }
        }
        occupiedWorkspaceIds = occupied;
    }

    Component.onCompleted: _refreshOccupiedWorkspaces()

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: workspacesModuleRoot._refreshOccupiedWorkspaces()
    }

    Connections {
        target: Hyprland
        function onFocusedWorkspaceChanged() { workspacesModuleRoot._refreshOccupiedWorkspaces(); }
    }

    spacing: 2

    Repeater {
        model: workspacesModuleRoot.slotsPerPage

        WorkspaceIndicator {
            id: workspaceIndicator

            required property int index

            readonly property int targetWorkspaceId: workspacesModuleRoot.currentPageStart + (workspacesModuleRoot.slotsPerPage - 1 - index)

            workspaceId: targetWorkspaceId
            isActive: targetWorkspaceId === workspacesModuleRoot.focusedWorkspaceId
            isOccupied: workspacesModuleRoot.occupiedWorkspaceIds[targetWorkspaceId] === true
            useWarningColor: index === workspacesModuleRoot.warningSlotIndex

            Layout.alignment: Qt.AlignHCenter

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: Hyprland.dispatch(`workspace ${workspaceIndicator.targetWorkspaceId}`)
            }
        }
    }
}
