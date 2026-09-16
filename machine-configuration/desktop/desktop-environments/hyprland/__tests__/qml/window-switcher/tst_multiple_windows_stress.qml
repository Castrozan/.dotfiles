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

        function test_fifteen_windows_same_workspace() {
            var toplevels = {};
            var clients = [];
            for (var i = 0; i < 15; i++) {
                var addr = "addr" + i;
                toplevels[addr] = {
                    wayland: "wl-" + addr
                };
                clients.push({
                    address: "0x" + addr,
                    title: "Window " + i,
                    "class": "app" + (i % 5),
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: i
                });
            }
            windowSwitcher.buildFilteredWindowListFromFreshData(JSON.stringify(clients), 1, toplevels);
            // All 15 windows shown (no deduplication in switcher)
            compare(windowSwitcher.windowList.length, 15);
            // Sorted by focusHistoryId
            compare(windowSwitcher.windowList[0].focusHistoryId, 0);
            compare(windowSwitcher.windowList[14].focusHistoryId, 14);
        }

        function test_no_windows_on_focused_workspace() {
            var toplevels = {
                "a": {
                    wayland: "wl-a"
                }
            };
            var clients = JSON.stringify([
                {
                    address: "0xa",
                    title: "Win",
                    "class": "app",
                    workspace: {
                        id: 2
                    },
                    focusHistoryID: 0
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_mixed_workspaces_only_focused_shown() {
            var toplevels = {
                "a": {
                    wayland: "wl-a"
                },
                "b": {
                    wayland: "wl-b"
                },
                "c": {
                    wayland: "wl-c"
                },
                "d": {
                    wayland: "wl-d"
                }
            };
            var clients = JSON.stringify([
                {
                    address: "0xa",
                    title: "WS1-A",
                    "class": "app1",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 0
                },
                {
                    address: "0xb",
                    title: "WS2-B",
                    "class": "app2",
                    workspace: {
                        id: 2
                    },
                    focusHistoryID: 1
                },
                {
                    address: "0xc",
                    title: "WS1-C",
                    "class": "app3",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 2
                },
                {
                    address: "0xd",
                    title: "WS3-D",
                    "class": "app4",
                    workspace: {
                        id: 3
                    },
                    focusHistoryID: 3
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 2);
            compare(windowSwitcher.windowList[0].title, "WS1-A");
            compare(windowSwitcher.windowList[1].title, "WS1-C");
        }

        function test_windows_missing_toplevels_are_filtered() {
            var toplevels = {
                "a": {
                    wayland: "wl-a"
                }
            };
            var clients = JSON.stringify([
                {
                    address: "0xa",
                    title: "Has Toplevel",
                    "class": "app1",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 0
                },
                {
                    address: "0xb",
                    title: "No Toplevel",
                    "class": "app2",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 1
                },
                {
                    address: "0xc",
                    title: "Also No",
                    "class": "app3",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 2
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 1);
            compare(windowSwitcher.windowList[0].title, "Has Toplevel");
        }
    }
}
