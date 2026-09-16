import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleClassNameEdgeCases"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_whitespace_only_class_is_not_filtered() {
            // class " " is truthy — passes the empty check
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": " ",
                    focusHistoryID: 0
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, " ");
        }

        function test_class_with_special_characters() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "org.mozilla.firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x2",
                    "class": "com.google.Chrome",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 2);
        }

        function test_case_sensitive_classes_are_separate() {
            // "Firefox" and "firefox" are different classes
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": "Firefox",
                    focusHistoryID: 0
                },
                {
                    address: "0x2",
                    "class": "firefox",
                    focusHistoryID: 1
                }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 2);
        }

        function test_null_class_treated_as_empty() {
            var clients = JSON.stringify([
                {
                    address: "0x1",
                    "class": null,
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
    }
}
