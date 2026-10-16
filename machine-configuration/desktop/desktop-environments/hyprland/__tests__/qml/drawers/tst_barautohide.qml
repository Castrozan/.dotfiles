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

        function initTestCase() {
            compare(hoverController.barAutoHideInterval, 6000);
        }

        function init() {
            drawerState.clearPopout();
            drawerState.closeAllPanels();
            drawerState.closeBar();
            drawerState.setBarHovered(false);
            hoverController.bar.triggerLeft();
            hoverController.bar.revealDelayInterval = 10;
            hoverController.bar.concealDelayInterval = 10;
            wait(40);
            hoverController.barAutoHideInterval = 30;
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

        function test_keyboard_reveal_expires_without_hover() {
            hoverController.toggleBarTemporarily();
            verify(drawerState.barVisible);
            tryVerify(() => !drawerState.barVisible, 400);
        }

        function test_second_keyboard_toggle_closes_the_bar() {
            hoverController.toggleBarTemporarily();
            verify(drawerState.barVisible);
            hoverController.toggleBarTemporarily();
            verify(!drawerState.barVisible);
            wait(60);
            verify(!drawerState.barVisible);
        }

        function test_keyboard_timeout_keeps_hovered_content_open() {
            hoverController.toggleBarTemporarily();
            hoverController.bar.contentEntered();
            wait(60);
            verify(drawerState.barVisible);
            hoverController.bar.contentLeft();
            tryVerify(() => !drawerState.barVisible, 400);
        }

        function test_keyboard_timeout_keeps_popout_open_until_dismissed() {
            hoverController.toggleBarTemporarily();
            drawerState.showPopout("network", 500);
            wait(60);
            verify(drawerState.barVisible);
            drawerState.clearPopout();
            tryVerify(() => !drawerState.barVisible, 400);
        }

        function test_keyboard_hide_cancels_pending_hover_reveal() {
            hoverController.bar.revealDelayInterval = 80;
            hoverController.bar.triggerEntered();
            hoverController.toggleBarTemporarily();
            hoverController.toggleBarTemporarily();
            wait(120);
            verify(!drawerState.barVisible);
        }

        function test_keyboard_reopen_cancels_pending_conceal() {
            hoverController.barAutoHideInterval = 100;
            drawerState.openBar();
            hoverController.bar.contentEntered();
            hoverController.bar.contentLeft();
            hoverController.toggleBarTemporarily();
            hoverController.toggleBarTemporarily();
            wait(40);
            verify(drawerState.barVisible);
            tryVerify(() => !drawerState.barVisible, 400);
        }

        function test_keyboard_hide_also_dismisses_popout() {
            drawerState.showPopout("network", 500);
            hoverController.toggleBarTemporarily();
            verify(!drawerState.barVisible);
            verify(!drawerState.hasActivePopout);
        }
    }
}
