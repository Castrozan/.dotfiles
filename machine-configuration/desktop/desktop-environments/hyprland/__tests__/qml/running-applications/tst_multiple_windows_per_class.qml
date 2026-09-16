import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleMultipleWindowsPerClass"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_five_windows_same_class_deduplicates_to_one() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 4
                },
                {
                    address: "0x2",
                    "class": "firefox",
                    focusHistoryID: 2
                },
                {
                    address: "0x3",
                    "class": "firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x4",
                    "class": "firefox",
                    focusHistoryID: 3
                },
                {
                    address: "0x5",
                    "class": "firefox",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            compare(runningAppsModule.runningAppsByClass[0].address, "0x3");
            compare(runningAppsModule.runningAppsByClass[0].focusHistoryID, 0);
        }

        function test_ten_windows_across_three_classes() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 5
                },
                {
                    address: "0x2",
                    "class": "firefox",
                    focusHistoryID: 2
                },
                {
                    address: "0x3",
                    "class": "firefox",
                    focusHistoryID: 8
                },
                {
                    address: "0x4",
                    "class": "kitty",
                    focusHistoryID: 0
                },
                {
                    address: "0x5",
                    "class": "kitty",
                    focusHistoryID: 3
                },
                {
                    address: "0x6",
                    "class": "kitty",
                    focusHistoryID: 7
                },
                {
                    address: "0x7",
                    "class": "kitty",
                    focusHistoryID: 9
                },
                {
                    address: "0x8",
                    "class": "code",
                    focusHistoryID: 1
                },
                {
                    address: "0x9",
                    "class": "code",
                    focusHistoryID: 4
                },
                {
                    address: "0xa",
                    "class": "code",
                    focusHistoryID: 6
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 3);

            // Each class should keep the window with lowest focusHistoryID
            var byClass = {};
            for (var i = 0; i < runningAppsModule.runningAppsByClass.length; i++) {
                var app = runningAppsModule.runningAppsByClass[i];
                byClass[app.windowClass] = app;
            }
            compare(byClass["firefox"].address, "0x2");
            compare(byClass["firefox"].focusHistoryID, 2);
            compare(byClass["kitty"].address, "0x4");
            compare(byClass["kitty"].focusHistoryID, 0);
            compare(byClass["code"].address, "0x8");
            compare(byClass["code"].focusHistoryID, 1);
        }

        function test_all_windows_same_class_same_focus_id() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 5
                },
                {
                    address: "0x2",
                    "class": "firefox",
                    focusHistoryID: 5
                },
                {
                    address: "0x3",
                    "class": "firefox",
                    focusHistoryID: 5
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            // First encountered wins when all equal (< is strict, so no replacement)
            compare(runningAppsModule.runningAppsByClass[0].address, "0x1");
        }

        function test_clicking_bar_focuses_most_recent_window_not_first() {
            // Simulates: 3 chrome windows, most recently focused is 0x2
            var clients = JSON.stringify([
                {
                    address: "0xold",
                    "class": "chrome-global",
                    focusHistoryID: 10
                },
                {
                    address: "0xrecent",
                    "class": "chrome-global",
                    focusHistoryID: 1
                },
                {
                    address: "0xolder",
                    "class": "chrome-global",
                    focusHistoryID: 5
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            // Bar stores the address of the most recently focused window
            compare(runningAppsModule.runningAppsByClass[0].address, "0xrecent");
        }
    }
}
