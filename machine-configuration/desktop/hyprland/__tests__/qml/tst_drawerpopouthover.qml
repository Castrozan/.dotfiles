import QtQuick
import QtTest
import "../../../quickshell/bar/program-configuration"

Item {
    id: root

    readonly property int concealTimeout: 1500
    readonly property int beyondConcealDelay: 700

    QtObject {
        id: fakePopoutAnchors

        function centerYForPopout(name) {
            return 42;
        }
    }

    DrawerState {
        id: drawerState

        popoutAnchorResolver: fakePopoutAnchors
    }

    DrawerHoverController {
        id: hoverController

        drawerState: drawerState
    }

    TestCase {
        name: "DrawerPopoutHoverSequences"

        function init() {
            hoverController.popoutContentEntered();
            drawerState.setPopoutHovered(false);
            drawerState.popoutIconHovered = false;
            hoverController.pointerOverBar = false;
            drawerState.showPopout("network", 10);
        }

        function test_pointer_enter_records_hover_on_the_state() {
            hoverController.popoutContentEntered();
            verify(drawerState.popoutHovered);
            hoverController.popoutContentLeft();
            verify(!drawerState.popoutHovered);
        }

        function test_pointer_leave_conceals_the_popout() {
            hoverController.popoutContentLeft();
            compare(drawerState.popoutCurrentName, "network");
            tryVerify(() => !drawerState.hasActivePopout, root.concealTimeout);
        }

        function test_pointer_re_enter_cancels_a_pending_conceal() {
            hoverController.popoutContentLeft();
            hoverController.popoutContentEntered();
            wait(root.beyondConcealDelay);
            compare(drawerState.popoutCurrentName, "network");
        }

        function test_showing_a_popout_cancels_a_pending_conceal() {
            hoverController.popoutContentLeft();
            drawerState.showPopout("battery", 20);
            wait(root.beyondConcealDelay);
            compare(drawerState.popoutCurrentName, "battery");
        }

        function test_pointer_over_the_bar_blocks_the_conceal() {
            hoverController.pointerOverBar = true;
            hoverController.popoutContentLeft();
            wait(root.beyondConcealDelay);
            compare(drawerState.popoutCurrentName, "network");
        }

        function test_hovered_popout_icon_blocks_the_conceal() {
            drawerState.popoutIconHovered = true;
            hoverController.popoutContentLeft();
            wait(root.beyondConcealDelay);
            compare(drawerState.popoutCurrentName, "network");
        }

        function test_hide_popout_intent_starts_the_conceal() {
            drawerState.hidePopout();
            compare(drawerState.popoutCurrentName, "network");
            tryVerify(() => !drawerState.hasActivePopout, root.concealTimeout);
        }
    }
}
