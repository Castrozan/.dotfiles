import QtQuick

Item {
    id: root

    property QtObject workspacesModule: QtObject {
        id: workspacesModule

        property int slotsPerPage: 7
        property int focusedWorkspaceId: 1

        readonly property int currentPageStart: Math.floor((focusedWorkspaceId - 1) / slotsPerPage) * slotsPerPage + 1

        property int warningSlotIndex: 3

        property var occupiedWorkspaceIds: ({})

        function refreshOccupiedWorkspaces(workspacesList) {
            var occupied = {};
            for (var i = 0; i < workspacesList.length; i++) {
                var ws = workspacesList[i];
                var windowCount = ws.lastIpcObject ? ws.lastIpcObject.windows : 0;
                if (windowCount > 0) {
                    occupied[ws.id] = true;
                }
            }
            occupiedWorkspaceIds = occupied;
        }

        function computeTargetWorkspaceIdForSlot(slotIndex) {
            return currentPageStart + (slotsPerPage - 1 - slotIndex);
        }

        function isSlotActive(slotIndex) {
            return computeTargetWorkspaceIdForSlot(slotIndex) === focusedWorkspaceId;
        }

        function isSlotOccupied(slotIndex) {
            var targetId = computeTargetWorkspaceIdForSlot(slotIndex);
            return occupiedWorkspaceIds[targetId] === true;
        }

        function isSlotWarning(slotIndex) {
            return slotIndex === warningSlotIndex;
        }
    }
}
