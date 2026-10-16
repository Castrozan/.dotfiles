import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/drawers"

Item {
    Component {
        id: workspaceFixture

        Item {
            property alias drawerState: drawerState
            property alias hoverController: hoverController

            QtObject {
                id: popoutAnchors

                function centerYForPopout(name) {
                    return 500;
                }
            }

            DrawerState {
                id: drawerState
                popoutAnchorResolver: popoutAnchors
            }

            DrawerHoverController {
                id: hoverController
                drawerState: drawerState
                activeWorkspaceId: 1
                barAutoHideInterval: 180
            }
        }
    }

    TestCase {
        id: workspaceTests
        name: "WorkspaceBarReveal"

        property var fixture

        function init() {
            fixture = createTemporaryObject(workspaceFixture, workspaceTests);
            verify(fixture !== null);
        }

        function test_initial_workspace_keeps_bar_hidden() {
            verify(!fixture.drawerState.barVisible);
            wait(220);
            verify(!fixture.drawerState.barVisible);
        }

        function test_workspace_change_reveals_then_expires() {
            fixture.hoverController.activeWorkspaceId = 2;
            verify(fixture.drawerState.barVisible);
            verify(!fixture.drawerState.hasAnyPanelVisible);
            tryVerify(() => !fixture.drawerState.barVisible, 500);
        }

        function test_latest_change_restarts_countdown_without_toggling() {
            fixture.hoverController.activeWorkspaceId = 2;
            wait(110);
            fixture.hoverController.activeWorkspaceId = 3;
            verify(fixture.drawerState.barVisible);
            wait(110);
            verify(fixture.drawerState.barVisible);
            tryVerify(() => !fixture.drawerState.barVisible, 500);
        }

        function test_workspace_reveal_cancels_pending_hover_conceal() {
            fixture.drawerState.openBar();
            fixture.hoverController.bar.concealDelayInterval = 10;
            fixture.hoverController.bar.contentEntered();
            fixture.hoverController.bar.contentLeft();
            fixture.hoverController.activeWorkspaceId = 2;
            wait(40);
            verify(fixture.drawerState.barVisible);
            tryVerify(() => !fixture.drawerState.barVisible, 500);
        }

        function test_missing_or_same_workspace_does_not_reveal() {
            fixture.hoverController.activeWorkspaceId = 0;
            fixture.hoverController.activeWorkspaceId = 1;
            verify(!fixture.drawerState.barVisible);
            fixture.hoverController.activeWorkspaceId = -5;
            verify(fixture.drawerState.barVisible);
        }

        function test_leaving_bar_does_not_shorten_workspace_countdown() {
            fixture.hoverController.activeWorkspaceId = 2;
            fixture.hoverController.bar.concealDelayInterval = 10;
            fixture.hoverController.bar.contentEntered();
            fixture.hoverController.bar.contentLeft();
            wait(40);
            verify(fixture.drawerState.barVisible);
            tryVerify(() => !fixture.drawerState.barVisible, 500);
        }

        function test_manual_toggle_closes_automatic_reveal() {
            fixture.hoverController.activeWorkspaceId = 2;
            fixture.hoverController.toggleBarTemporarily();
            verify(!fixture.drawerState.barVisible);
            wait(220);
            verify(!fixture.drawerState.barVisible);
        }
    }
}
