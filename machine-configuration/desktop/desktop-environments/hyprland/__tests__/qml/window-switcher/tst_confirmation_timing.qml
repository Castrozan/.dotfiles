import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

    TestCase {
        name: "WindowSwitcherStateMachineEdgeCases"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_double_confirm_when_overlay_hidden() {
            // Confirm twice before overlay opens — flag set once, second is noop (flag already true)
            windowSwitcher.confirmSelection();
            verify(windowSwitcher.confirmRequestedBeforeOverlayReady);
            windowSwitcher.confirmSelection();
            verify(windowSwitcher.confirmRequestedBeforeOverlayReady);
        }

        function test_confirm_after_cancel_sets_flag() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.cancelSwitcher();
            // Now overlay is hidden, confirm should set the pre-ready flag
            windowSwitcher.confirmSelection();
            verify(windowSwitcher.confirmRequestedBeforeOverlayReady);
        }

        function test_finish_open_with_confirm_before_ready_and_single_window() {
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                }
            ];
            windowSwitcher.finishOpenSwitcher();
            verify(!windowSwitcher.overlayVisible);
            verify(!windowSwitcher.confirmRequestedBeforeOverlayReady);
            compare(windowSwitcher.windowList.length, 0);
            compare(windowSwitcher.submapResetDispatchCount, 1);
            compare(windowSwitcher.lastFocusedWindowAddress, "a");
        }

        function test_finish_open_empty_list_with_confirm_before_ready() {
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;
            windowSwitcher.finishOpenSwitcher();
            // Empty list — early return, flag NOT cleared
            verify(windowSwitcher.confirmRequestedBeforeOverlayReady);
            verify(!windowSwitcher.overlayVisible);
        }

        function test_open_cancel_open_confirm_sequence() {
            var toplevels = {
                "a": {
                    wayland: "wl-a"
                },
                "b": {
                    wayland: "wl-b"
                }
            };
            var clients = JSON.stringify([
                {
                    address: "0xa",
                    title: "Win A",
                    "class": "app1",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 0
                },
                {
                    address: "0xb",
                    title: "Win B",
                    "class": "app2",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 1
                }
            ]);

            // Open
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);
            compare(windowSwitcher.selectedIndex, 1);

            // Cancel
            windowSwitcher.cancelSwitcher();
            verify(!windowSwitcher.overlayVisible);
            compare(windowSwitcher.windowList.length, 0);

            // Open again
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);
            compare(windowSwitcher.selectedIndex, 1);

            // Confirm
            windowSwitcher.confirmSelection();
            verify(!windowSwitcher.overlayVisible);
        }
    }
}
