import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/drawers"

Item {
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
    }

    TestCase {
        name: "BarAutoHide"

        function init() {
            drawerState.clearPopout();
            drawerState.closeAllPanels();
            drawerState.closeBar();
            drawerState.setBarHovered(false);
            hoverController.bar.triggerLeft();
            hoverController.bar.revealDelayInterval = 10;
            hoverController.bar.concealDelayInterval = 10;
            wait(40);
        }

        function test_hidden_bar_does_not_take_keyboard_focus() {
            verify(!drawerState.barVisible);
            drawerState.openBar();
            verify(drawerState.barVisible);
            verify(!drawerState.hasAnyPanelVisible);
        }

        function test_passing_the_edge_does_not_reveal_the_bar() {
            hoverController.bar.triggerEntered();
            hoverController.bar.triggerLeft();
            wait(40);
            verify(!drawerState.barVisible);
        }

        function test_edge_hover_reveals_then_leaving_hides() {
            hoverController.bar.triggerEntered();
            verify(!drawerState.barVisible);
            tryVerify(() => drawerState.barVisible, 400);
            hoverController.bar.triggerLeft();
            tryVerify(() => !drawerState.barVisible, 400);
        }

        function test_moving_from_edge_to_content_keeps_the_bar_open() {
            hoverController.bar.triggerEntered();
            tryVerify(() => drawerState.barVisible, 400);
            hoverController.bar.contentEntered();
            hoverController.bar.triggerLeft();
            wait(40);
            verify(drawerState.barVisible);
            hoverController.bar.contentLeft();
            tryVerify(() => !drawerState.barVisible, 400);
        }

        function test_popout_keeps_bar_open_until_dismissed() {
            drawerState.showPopout("network", 500);
            verify(drawerState.barVisible);
            hoverController.bar.contentEntered();
            hoverController.bar.contentLeft();
            wait(40);
            verify(drawerState.barVisible);
            drawerState.clearPopout();
            tryVerify(() => !drawerState.barVisible, 400);
        }

        function test_dismissing_popout_while_over_bar_keeps_bar_open() {
            drawerState.showPopout("network", 500);
            hoverController.bar.contentEntered();
            drawerState.clearPopout();
            wait(40);
            verify(drawerState.barVisible);
            hoverController.bar.contentLeft();
            tryVerify(() => !drawerState.barVisible, 400);
        }

        function test_returning_to_content_cancels_hiding() {
            drawerState.openBar();
            hoverController.bar.contentEntered();
            hoverController.bar.contentLeft();
            hoverController.bar.contentEntered();
            wait(40);
            verify(drawerState.barVisible);
        }
    }
}
