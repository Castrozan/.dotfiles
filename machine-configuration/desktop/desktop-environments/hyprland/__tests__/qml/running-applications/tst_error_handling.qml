import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleErrorHandling"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_invalid_json_does_not_change_state() {
            runningAppsModule.runningAppsByClass = [
                {
                    windowClass: "existing"
                }
            ];
            runningAppsModule.parseClientsAndRebuildAppList("not valid json");
            compare(runningAppsModule.runningAppsByClass.length, 1);
        }

        function test_empty_clients_produces_empty_list() {
            runningAppsModule.parseClientsAndRebuildAppList("[]");
            compare(runningAppsModule.runningAppsByClass.length, 0);
        }
    }
}
