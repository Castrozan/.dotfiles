import QtQuick
import QtTest

WorkspacePagesFixture {
    id: root

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
}
