import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleSequentialUpdatesConsistency"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_repeated_identical_updates_idempotent() {
            var clients = JSON.stringify([
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
            // Parse same data 5 times
            for (var i = 0; i < 5; i++) {
                runningAppsModule.parseClientsAndRebuildAppList(clients);
            }
            compare(runningAppsModule.runningAppsByClass.length, 2);
            compare(runningAppsModule.focusedWindowClass, "firefox");
            compare(runningAppsModule.firstSeenOrderByClass["firefox"], 0);
            compare(runningAppsModule.firstSeenOrderByClass["kitty"], 1);
            // Index should still be 2 (not incremented on re-seen)
            compare(runningAppsModule.firstSeenOrderNextIndex, 2);
        }

        function test_address_changes_for_same_class_across_updates() {
            // Simulate window being replaced (close + open between refreshes)
            var batch1 = JSON.stringify([
                {
                    address: "0xold",
                    "class": "firefox",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.runningAppsByClass[0].address, "0xold");

            var batch2 = JSON.stringify([
                {
                    address: "0xnew",
                    "class": "firefox",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            compare(runningAppsModule.runningAppsByClass[0].address, "0xnew");
            // Same first-seen index
            compare(runningAppsModule.firstSeenOrderByClass["firefox"], 0);
            compare(runningAppsModule.firstSeenOrderNextIndex, 1);
        }

        function test_gradual_buildup_from_empty() {
            // Simulate boot: windows appear one by one
            var classes = ["firefox", "kitty", "code", "slack", "chrome-global"];
            for (var i = 0; i < classes.length; i++) {
                var clients = [];
                for (var j = 0; j <= i; j++) {
                    clients.push({
                        address: "0x" + j,
                        "class": classes[j],
                        focusHistoryID: i - j
                    });
                }
                runningAppsModule.parseClientsAndRebuildAppList(JSON.stringify(clients));
                compare(runningAppsModule.runningAppsByClass.length, i + 1);
            }
            // Final order should be stable first-seen: firefox, kitty, code, slack, chrome-global
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "firefox");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass[2].windowClass, "code");
            compare(runningAppsModule.runningAppsByClass[3].windowClass, "slack");
            compare(runningAppsModule.runningAppsByClass[4].windowClass, "chrome-global");
        }
    }
}
