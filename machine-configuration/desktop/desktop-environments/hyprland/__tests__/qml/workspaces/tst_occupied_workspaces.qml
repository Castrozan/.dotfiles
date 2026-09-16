import QtQuick
import QtTest

WorkspacePagesFixture {
    id: root

    TestCase {
        name: "WorkspacesModuleOccupiedWorkspaces"

        function init() {
            workspacesModule.focusedWorkspaceId = 1;
            workspacesModule.occupiedWorkspaceIds = {};
        }

        function test_refresh_marks_workspaces_with_windows() {
            workspacesModule.refreshOccupiedWorkspaces([
                {
                    id: 1,
                    lastIpcObject: {
                        windows: 3
                    }
                },
                {
                    id: 2,
                    lastIpcObject: {
                        windows: 0
                    }
                },
                {
                    id: 3,
                    lastIpcObject: {
                        windows: 1
                    }
                }
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
                {
                    id: 1,
                    lastIpcObject: null
                },
                {
                    id: 2
                }
            ]);
            compare(workspacesModule.occupiedWorkspaceIds[1], undefined);
            compare(workspacesModule.occupiedWorkspaceIds[2], undefined);
        }

        function test_slot_occupied_reflects_workspace_state() {
            workspacesModule.occupiedWorkspaceIds = {
                1: true,
                3: true,
                5: true
            };
            verify(workspacesModule.isSlotOccupied(6));
            verify(!workspacesModule.isSlotOccupied(5));
            verify(workspacesModule.isSlotOccupied(4));
        }

        function test_refresh_replaces_previous_state() {
            workspacesModule.occupiedWorkspaceIds = {
                1: true,
                2: true,
                3: true
            };
            workspacesModule.refreshOccupiedWorkspaces([
                {
                    id: 5,
                    lastIpcObject: {
                        windows: 1
                    }
                }
            ]);
            compare(workspacesModule.occupiedWorkspaceIds[1], undefined);
            compare(workspacesModule.occupiedWorkspaceIds[5], true);
        }
    }
}
