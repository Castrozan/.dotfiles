import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleDeduplication"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_deduplicates_same_class_windows() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 2
                },
                {
                    address: "0x2",
                    "class": "firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x3",
                    "class": "kitty",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 2);
        }

        function test_keeps_most_recently_focused_window_per_class() {
            var clients = JSON.stringify([
                {
                    address: "0xold",
                    "class": "firefox",
                    focusHistoryID: 5
                },
                {
                    address: "0xnew",
                    "class": "firefox",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass[0].address, "0xnew");
        }

        function test_skips_clients_with_empty_class() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "",
                    focusHistoryID: 0
                },
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "kitty");
        }

        function test_skips_clients_without_class() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    focusHistoryID: 0
                },
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
        }

        function test_defaults_focus_history_to_9999_when_missing() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox"
                },
                {
                    address: "0x2",
                    "class": "firefox",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass[0].address, "0x2");
        }
    }
}
