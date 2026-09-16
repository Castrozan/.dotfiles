import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleAutoOpenedWindows"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_all_windows_auto_opened_no_focus_history() {
            // Windows opened by startup scripts — none ever focused
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox"
                },
                {
                    address: "0x2",
                    "class": "kitty"
                },
                {
                    address: "0x3",
                    "class": "code"
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 3);
            compare(runningAppsModule.focusedWindowClass, "");
            // All get 9999, ordering is first-seen
            for (var i = 0; i < runningAppsModule.runningAppsByClass.length; i++) {
                compare(runningAppsModule.runningAppsByClass[i].focusHistoryID, 9999);
            }
        }

        function test_auto_opened_then_one_focused() {
            // First batch: all auto-opened
            var batch1 = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox"
                },
                {
                    address: "0x2",
                    "class": "kitty"
                },
                {
                    address: "0x3",
                    "class": "code"
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.focusedWindowClass, "");

            // Second batch: user clicked kitty
            var batch2 = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 1
                },
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 0
                },
                {
                    address: "0x3",
                    "class": "code",
                    focusHistoryID: 2
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            compare(runningAppsModule.focusedWindowClass, "kitty");
            // Order preserved: firefox, kitty, code (first-seen)
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "firefox");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass[2].windowClass, "code");
        }

        function test_mix_of_auto_opened_and_focused_same_class() {
            // 3 firefox: one focused, two never touched
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox"
                },
                {
                    address: "0x2",
                    "class": "firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x3",
                    "class": "firefox"
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            compare(runningAppsModule.runningAppsByClass[0].address, "0x2");
            compare(runningAppsModule.focusedWindowClass, "firefox");
        }
    }
}
