import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleRapidLifecycle"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_app_close_and_reopen_gets_new_position() {
            // firefox opened first
            var batch1 = JSON.stringify([
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
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.firstSeenOrderByClass["firefox"], 0);
            compare(runningAppsModule.firstSeenOrderByClass["kitty"], 1);

            // firefox closed
            var batch2 = JSON.stringify([
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            verify(runningAppsModule.firstSeenOrderByClass["firefox"] === undefined);

            // firefox reopened — should be AFTER kitty now
            var batch3 = JSON.stringify([
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 1
                },
                {
                    address: "0x3",
                    "class": "firefox",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch3);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "firefox");
        }

        function test_rapid_open_close_ten_cycles() {
            // Simulate 10 cycles of apps appearing and disappearing
            for (var cycle = 0; cycle < 10; cycle++) {
                var clients = [];
                // Each cycle has a different set of 3 apps from a pool of 5
                var allClasses = ["firefox", "kitty", "code", "chrome-global", "slack"];
                for (var j = 0; j < 3; j++) {
                    var idx = (cycle + j) % 5;
                    clients.push({
                        address: "0x" + (cycle * 10 + j),
                        "class": allClasses[idx],
                        focusHistoryID: j
                    });
                }
                runningAppsModule.parseClientsAndRebuildAppList(JSON.stringify(clients));
                compare(runningAppsModule.runningAppsByClass.length, 3);
            }
            // After all cycles, state should be consistent
            verify(runningAppsModule.firstSeenOrderNextIndex > 0);
            // Exactly 3 entries in firstSeenOrder (matching current 3 apps)
            var orderCount = 0;
            for (var k in runningAppsModule.firstSeenOrderByClass)
                orderCount++;
            compare(orderCount, 3);
        }

        function test_all_apps_close_then_reopen() {
            var batch1 = JSON.stringify([
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
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.runningAppsByClass.length, 2);

            // All close
            runningAppsModule.parseClientsAndRebuildAppList("[]");
            compare(runningAppsModule.runningAppsByClass.length, 0);
            compare(runningAppsModule.focusedWindowClass, "");

            // Reopen in different order
            var batch2 = JSON.stringify([
                {
                    address: "0x3",
                    "class": "kitty",
                    focusHistoryID: 0
                },
                {
                    address: "0x4",
                    "class": "firefox",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            // New first-seen order: kitty first now
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "firefox");
        }

        function test_firstseenorder_index_grows_monotonically() {
            var batch1 = JSON.stringify([
                {
                    address: "0x1",
                    "class": "a",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.firstSeenOrderNextIndex, 1);

            // Close a, open b
            var batch2 = JSON.stringify([
                {
                    address: "0x2",
                    "class": "b",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            compare(runningAppsModule.firstSeenOrderNextIndex, 2);

            // Close b, open c
            var batch3 = JSON.stringify([
                {
                    address: "0x3",
                    "class": "c",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch3);
            compare(runningAppsModule.firstSeenOrderNextIndex, 3);

        // Index never resets, always grows
        // After 1000 cycles this would be 1000 — acceptable for a session
        }
    }
}
