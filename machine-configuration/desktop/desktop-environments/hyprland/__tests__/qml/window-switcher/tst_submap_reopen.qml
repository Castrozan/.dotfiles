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

        function test_submap_desync_scenario_card_click_then_reopen() {
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

            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);

            windowSwitcher.selectedIndex = 0;
            windowSwitcher.confirmSelection();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            verify(!windowSwitcher.overlayVisible);
            compare(windowSwitcher.windowList.length, 0);

            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);
            compare(windowSwitcher.selectedIndex, 1);
        }

        function test_submap_desync_scenario_click_outside_then_reopen() {
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

            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);

            windowSwitcher.cancelSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            verify(!windowSwitcher.overlayVisible);

            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);
            compare(windowSwitcher.selectedIndex, 1);
        }

        function test_multiple_close_cycles_dispatch_each_time() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.cancelSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 1);

            windowSwitcher.windowList = [
                {
                    address: "b",
                    title: "W2"
                }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.confirmSelection();
            compare(windowSwitcher.submapResetDispatchCount, 2);

            windowSwitcher.windowList = [
                {
                    address: "c",
                    title: "W3"
                }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.cancelSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 3);
        }
    }
}
