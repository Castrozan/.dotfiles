import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

    TestCase {
        name: "WindowSwitcherMultipleWindowsStress"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_all_windows_same_focus_id() {
            var toplevels = {
                "a": {
                    wayland: "wl-a"
                },
                "b": {
                    wayland: "wl-b"
                },
                "c": {
                    wayland: "wl-c"
                }
            };
            var clients = JSON.stringify([
                {
                    address: "0xa",
                    title: "Win A",
                    "class": "app",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 5
                },
                {
                    address: "0xb",
                    title: "Win B",
                    "class": "app",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 5
                },
                {
                    address: "0xc",
                    title: "Win C",
                    "class": "app",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 5
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 3);
        // All have same focusHistoryId — sort is stable, order depends on implementation
        }

        function test_all_windows_no_focus_history() {
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
                    title: "Auto1",
                    "class": "app1",
                    workspace: {
                        id: 1
                    }
                },
                {
                    address: "0xb",
                    title: "Auto2",
                    "class": "app2",
                    workspace: {
                        id: 1
                    }
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 2);
            compare(windowSwitcher.windowList[0].focusHistoryId, 9999);
            compare(windowSwitcher.windowList[1].focusHistoryId, 9999);
        }
    }
}
