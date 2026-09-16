import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleFirstSeenOrdering"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_preserves_first_seen_order_across_updates() {
            var firstBatch = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(firstBatch);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "firefox");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "kitty");

            var secondBatch = JSON.stringify([
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 0
                },
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 1
                },
                {
                    address: "0x3",
                    "class": "code",
                    focusHistoryID: 2
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(secondBatch);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "firefox");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass[2].windowClass, "code");
        }

        function test_removes_closed_apps_from_first_seen_order() {
            var firstBatch = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 1
                },
                {
                    address: "0x3",
                    "class": "code",
                    focusHistoryID: 2
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(firstBatch);

            var secondBatch = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x3",
                    "class": "code",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(secondBatch);
            compare(runningAppsModule.runningAppsByClass.length, 2);
            compare(runningAppsModule.firstSeenOrderByClass["kitty"], undefined);
        }

        function test_new_app_gets_next_index() {
            var firstBatch = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(firstBatch);
            compare(runningAppsModule.firstSeenOrderByClass["firefox"], 0);
            compare(runningAppsModule.firstSeenOrderNextIndex, 1);

            var secondBatch = JSON.stringify([
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
            runningAppsModule.parseClientsAndRebuildAppList(secondBatch);
            compare(runningAppsModule.firstSeenOrderByClass["kitty"], 1);
            compare(runningAppsModule.firstSeenOrderNextIndex, 2);
        }
    }
}
