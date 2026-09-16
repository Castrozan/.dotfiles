import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleFocusDetection"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_detects_focused_window_class() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 1
                },
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.focusedWindowClass, "kitty");
        }

        function test_no_focused_window_when_no_zero_history() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 1
                },
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 2
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.focusedWindowClass, "");
        }

        function test_empty_clients_clears_focused_class() {
            runningAppsModule.focusedWindowClass = "old";
            runningAppsModule.parseClientsAndRebuildAppList("[]");
            compare(runningAppsModule.focusedWindowClass, "");
        }
    }
}
