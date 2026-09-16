import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

    TestCase {
        name: "WindowSwitcherSubmapResetOnClose"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_confirm_dispatches_submap_reset_and_focuses_selected() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                },
                {
                    address: "b",
                    title: "W2"
                }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.selectedIndex = 1;

            windowSwitcher.confirmSelection();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            compare(windowSwitcher.lastFocusedWindowAddress, "b");
        }

        function test_cancel_dispatches_submap_reset() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                },
                {
                    address: "b",
                    title: "W2"
                }
            ];
            windowSwitcher.overlayVisible = true;

            windowSwitcher.cancelSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 1);
        }

        function test_card_click_then_confirm_dispatches_submap_reset() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                },
                {
                    address: "b",
                    title: "W2"
                }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.selectedIndex = 0;

            windowSwitcher.confirmSelection();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            verify(!windowSwitcher.overlayVisible);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_quick_switch_dispatches_submap_reset_and_focuses_window() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                },
                {
                    address: "b",
                    title: "W2"
                }
            ];
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;

            windowSwitcher.finishOpenSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            verify(!windowSwitcher.overlayVisible);
            compare(windowSwitcher.lastFocusedWindowAddress, "b");
        }

        function test_close_switcher_resets_all_state() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                },
                {
                    address: "b",
                    title: "W2"
                }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.selectedIndex = 1;
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;

            windowSwitcher.closeSwitcher();

            verify(!windowSwitcher.overlayVisible);
            verify(!windowSwitcher.confirmRequestedBeforeOverlayReady);
            compare(windowSwitcher.windowList.length, 0);
            compare(windowSwitcher.selectedIndex, 0);
            compare(windowSwitcher.submapResetDispatchCount, 1);
        }
    }
}
