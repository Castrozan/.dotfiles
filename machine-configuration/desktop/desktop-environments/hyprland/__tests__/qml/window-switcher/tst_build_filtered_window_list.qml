import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

    TestCase {
        name: "WindowSwitcherBuildFilteredWindowList"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_filters_windows_by_workspace() {
            windowSwitcher.buildFilteredWindowListFromFreshData(root.sampleClientsJson, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList.length, 2);
        }

        function test_strips_hex_prefix_from_address() {
            windowSwitcher.buildFilteredWindowListFromFreshData(root.sampleClientsJson, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList[0].address, "def456");
        }

        function test_sorts_by_focus_history_id_ascending() {
            windowSwitcher.buildFilteredWindowListFromFreshData(root.sampleClientsJson, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList[0].title, "Terminal");
            compare(windowSwitcher.windowList[1].title, "Firefox");
        }

        function test_skips_clients_without_toplevel() {
            var clients = JSON.stringify([
                {
                    address: "0xunknown",
                    title: "Ghost",
                    "class": "ghost",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 0
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_skips_clients_without_workspace() {
            var clients = JSON.stringify([
                {
                    address: "0xabc123",
                    title: "Orphan",
                    "class": "orphan",
                    focusHistoryID: 0
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_uses_class_as_title_fallback() {
            var clients = JSON.stringify([
                {
                    address: "0xabc123",
                    title: "",
                    "class": "fallback-class",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 0
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList[0].title, "fallback-class");
        }

        function test_uses_unknown_when_no_title_or_class() {
            var clients = JSON.stringify([
                {
                    address: "0xabc123",
                    title: "",
                    "class": "",
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 0
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList[0].title, "Unknown");
        }

        function test_handles_invalid_json() {
            windowSwitcher.windowList = [
                {
                    address: "existing"
                }
            ];
            windowSwitcher.buildFilteredWindowListFromFreshData("not valid json", 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList.length, 1);
        }

        function test_handles_empty_clients_list() {
            windowSwitcher.buildFilteredWindowListFromFreshData("[]", 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_defaults_focus_history_id_to_9999_when_missing() {
            var clients = JSON.stringify([
                {
                    address: "0xabc123",
                    title: "NoHistory",
                    "class": "app",
                    workspace: {
                        id: 1
                    }
                }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList[0].focusHistoryId, 9999);
        }

        function test_preserves_window_class() {
            windowSwitcher.buildFilteredWindowListFromFreshData(root.sampleClientsJson, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList[0].windowClass, "kitty");
            compare(windowSwitcher.windowList[1].windowClass, "firefox");
        }
    }
}
