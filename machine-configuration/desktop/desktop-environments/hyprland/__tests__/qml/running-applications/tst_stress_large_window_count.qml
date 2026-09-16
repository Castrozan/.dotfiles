import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleStressLargeWindowCount"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_fifty_windows_across_ten_classes() {
            var clients = [];
            for (var i = 0; i < 50; i++) {
                clients.push({
                    address: "0x" + i,
                    "class": "app" + (i % 10),
                    focusHistoryID: i
                });
            }
            runningAppsModule.parseClientsAndRebuildAppList(JSON.stringify(clients));
            compare(runningAppsModule.runningAppsByClass.length, 10);

            // app0 should have address 0x0 (focusHistoryID 0, lowest among 0,10,20,30,40)
            var byClass = {};
            for (var j = 0; j < runningAppsModule.runningAppsByClass.length; j++) {
                var app = runningAppsModule.runningAppsByClass[j];
                byClass[app.windowClass] = app;
            }
            compare(byClass["app0"].address, "0x0");
            compare(byClass["app0"].focusHistoryID, 0);
            compare(byClass["app1"].address, "0x1");
            compare(byClass["app1"].focusHistoryID, 1);
            compare(byClass["app9"].address, "0x9");
            compare(byClass["app9"].focusHistoryID, 9);
        }

        function test_hundred_windows_single_class() {
            var clients = [];
            for (var i = 0; i < 100; i++) {
                clients.push({
                    address: "0x" + i,
                    "class": "chrome-global",
                    focusHistoryID: 99 - i
                });
            }
            runningAppsModule.parseClientsAndRebuildAppList(JSON.stringify(clients));
            compare(runningAppsModule.runningAppsByClass.length, 1);
            // Window with focusHistoryID 0 is 0x99
            compare(runningAppsModule.runningAppsByClass[0].address, "0x99");
            compare(runningAppsModule.runningAppsByClass[0].focusHistoryID, 0);
        }

        function test_twenty_unique_classes_ordering_stable() {
            var clients = [];
            for (var i = 0; i < 20; i++) {
                clients.push({
                    address: "0x" + i,
                    "class": "class" + i,
                    focusHistoryID: 19 - i
                });
            }
            runningAppsModule.parseClientsAndRebuildAppList(JSON.stringify(clients));
            compare(runningAppsModule.runningAppsByClass.length, 20);

            // Second parse with same classes but different order shouldn't change first-seen
            var clients2 = [];
            for (var j = 19; j >= 0; j--) {
                clients2.push({
                    address: "0x" + (j + 100),
                    "class": "class" + j,
                    focusHistoryID: j
                });
            }
            runningAppsModule.parseClientsAndRebuildAppList(JSON.stringify(clients2));
            compare(runningAppsModule.runningAppsByClass.length, 20);
            // First-seen order preserved from initial parse
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "class0");
            compare(runningAppsModule.runningAppsByClass[19].windowClass, "class19");
        }
    }
}
