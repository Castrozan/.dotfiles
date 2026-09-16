import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleFocusEdgeCases"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_multiple_focus_id_zero_different_classes() {
            // Hyprland bug: two windows claim focus
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x2",
                    "class": "kitty",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            // Last one encountered wins for focusedWindowClass
            compare(runningAppsModule.focusedWindowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass.length, 2);
        }

        function test_multiple_focus_id_zero_same_class() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x2",
                    "class": "firefox",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            // First wins (0 < 0 is false, so no replacement)
            compare(runningAppsModule.runningAppsByClass[0].address, "0x1");
            compare(runningAppsModule.focusedWindowClass, "firefox");
        }

        function test_focus_switches_between_updates() {
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
            compare(runningAppsModule.focusedWindowClass, "firefox");

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
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            compare(runningAppsModule.focusedWindowClass, "kitty");
            // Order unchanged
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "firefox");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "kitty");
        }
    }
}
