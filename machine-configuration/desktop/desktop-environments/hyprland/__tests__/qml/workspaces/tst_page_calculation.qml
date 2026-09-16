import QtQuick
import QtTest

WorkspacePagesFixture {
    id: root

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
}
