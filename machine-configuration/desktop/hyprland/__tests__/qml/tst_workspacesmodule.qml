import QtQuick
import QtTest

Item {
    id: root

    QtObject {
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

    TestCase {
        name: "WorkspacesModulePageCalculation"

        function test_first_page_starts_at_1() {
            workspacesModule.focusedWorkspaceId = 1;
            compare(workspacesModule.currentPageStart, 1);
        }

        function test_workspace_7_is_still_first_page() {
            workspacesModule.focusedWorkspaceId = 7;
            compare(workspacesModule.currentPageStart, 1);
        }

        function test_workspace_8_starts_second_page() {
            workspacesModule.focusedWorkspaceId = 8;
            compare(workspacesModule.currentPageStart, 8);
        }

        function test_workspace_14_is_second_page() {
            workspacesModule.focusedWorkspaceId = 14;
            compare(workspacesModule.currentPageStart, 8);
        }

        function test_workspace_15_starts_third_page() {
            workspacesModule.focusedWorkspaceId = 15;
            compare(workspacesModule.currentPageStart, 15);
        }

        function test_workspace_3_is_first_page() {
            workspacesModule.focusedWorkspaceId = 3;
            compare(workspacesModule.currentPageStart, 1);
        }
    }

    TestCase {
        name: "WorkspacesModuleSlotMapping"

        function init() {
            workspacesModule.focusedWorkspaceId = 1;
        }

        function test_slot_0_maps_to_highest_workspace_in_page() {
            compare(workspacesModule.computeTargetWorkspaceIdForSlot(0), 7);
        }

        function test_slot_6_maps_to_lowest_workspace_in_page() {
            compare(workspacesModule.computeTargetWorkspaceIdForSlot(6), 1);
        }

        function test_slot_ordering_is_reversed() {
            var ids = [];
            for (var i = 0; i < 7; i++) {
                ids.push(workspacesModule.computeTargetWorkspaceIdForSlot(i));
            }
            compare(ids, [7, 6, 5, 4, 3, 2, 1]);
        }

        function test_second_page_slot_mapping() {
            workspacesModule.focusedWorkspaceId = 10;
            compare(workspacesModule.computeTargetWorkspaceIdForSlot(0), 14);
            compare(workspacesModule.computeTargetWorkspaceIdForSlot(6), 8);
        }
    }

    TestCase {
        name: "WorkspacesModuleActiveSlot"

        function test_workspace_1_active_slot_is_last() {
            workspacesModule.focusedWorkspaceId = 1;
            verify(workspacesModule.isSlotActive(6));
            verify(!workspacesModule.isSlotActive(0));
            verify(!workspacesModule.isSlotActive(3));
        }

        function test_workspace_4_active_slot_is_middle() {
            workspacesModule.focusedWorkspaceId = 4;
            verify(workspacesModule.isSlotActive(3));
        }

        function test_workspace_7_active_slot_is_first() {
            workspacesModule.focusedWorkspaceId = 7;
            verify(workspacesModule.isSlotActive(0));
        }

        function test_only_one_slot_is_active() {
            workspacesModule.focusedWorkspaceId = 3;
            var activeCount = 0;
            for (var i = 0; i < 7; i++) {
                if (workspacesModule.isSlotActive(i))
                    activeCount++;
            }
            compare(activeCount, 1);
        }
    }

    TestCase {
        name: "WorkspacesModuleOccupiedWorkspaces"

        function init() {
            workspacesModule.focusedWorkspaceId = 1;
            workspacesModule.occupiedWorkspaceIds = {};
        }

        function test_refresh_marks_workspaces_with_windows() {
            workspacesModule.refreshOccupiedWorkspaces([
                { id: 1, lastIpcObject: { windows: 3 } },
                { id: 2, lastIpcObject: { windows: 0 } },
                { id: 3, lastIpcObject: { windows: 1 } }
            ]);
            compare(workspacesModule.occupiedWorkspaceIds[1], true);
            compare(workspacesModule.occupiedWorkspaceIds[2], undefined);
            compare(workspacesModule.occupiedWorkspaceIds[3], true);
        }

        function test_refresh_handles_empty_workspaces_list() {
            workspacesModule.refreshOccupiedWorkspaces([]);
            var keys = Object.keys(workspacesModule.occupiedWorkspaceIds);
            compare(keys.length, 0);
        }

        function test_refresh_handles_missing_ipc_object() {
            workspacesModule.refreshOccupiedWorkspaces([
                { id: 1, lastIpcObject: null },
                { id: 2 }
            ]);
            compare(workspacesModule.occupiedWorkspaceIds[1], undefined);
            compare(workspacesModule.occupiedWorkspaceIds[2], undefined);
        }

        function test_slot_occupied_reflects_workspace_state() {
            workspacesModule.occupiedWorkspaceIds = { 1: true, 3: true, 5: true };
            verify(workspacesModule.isSlotOccupied(6));
            verify(!workspacesModule.isSlotOccupied(5));
            verify(workspacesModule.isSlotOccupied(4));
        }

        function test_refresh_replaces_previous_state() {
            workspacesModule.occupiedWorkspaceIds = { 1: true, 2: true, 3: true };
            workspacesModule.refreshOccupiedWorkspaces([
                { id: 5, lastIpcObject: { windows: 1 } }
            ]);
            compare(workspacesModule.occupiedWorkspaceIds[1], undefined);
            compare(workspacesModule.occupiedWorkspaceIds[5], true);
        }
    }

    TestCase {
        name: "WorkspacesModuleWarningSlot"

        function test_warning_slot_is_index_3() {
            compare(workspacesModule.warningSlotIndex, 3);
        }

        function test_only_warning_slot_returns_true() {
            for (var i = 0; i < 7; i++) {
                if (i === 3)
                    verify(workspacesModule.isSlotWarning(i));
                else
                    verify(!workspacesModule.isSlotWarning(i));
            }
        }
    }
}
