import QtQuick
import QtTest

WorkspacePagesFixture {
    id: root

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
}
