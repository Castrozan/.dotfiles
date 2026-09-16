import QtQuick
import QtTest

LauncherApplicationsFixture {
    id: root

    TestCase {
        name: "LauncherAppsServiceAllApplicationsSorted"

        function init() {
            launcherAppsService.usageHistoryByAppId = {};
        }

        function test_sorts_alphabetically_when_no_usage() {
            var results = launcherAppsService.allApplicationsSorted(root.sampleApplications);
            compare(results.length, 5);
            compare(results[0].id, "chromium");
            compare(results[1].id, "nautilus");
            compare(results[2].id, "firefox");
            compare(results[3].id, "kitty");
            compare(results[4].id, "code");
        }

        function test_sorts_most_recently_used_first() {
            launcherAppsService.usageHistoryByAppId = {
                "kitty": 5000,
                "firefox": 3000,
                "code": 1000
            };
            var results = launcherAppsService.allApplicationsSorted(root.sampleApplications);
            compare(results[0].id, "kitty");
            compare(results[1].id, "firefox");
            compare(results[2].id, "code");
        }

        function test_unused_apps_sorted_alphabetically_after_used() {
            launcherAppsService.usageHistoryByAppId = {
                "kitty": 5000
            };
            var results = launcherAppsService.allApplicationsSorted(root.sampleApplications);
            compare(results[0].id, "kitty");
            compare(results[1].id, "chromium");
        }

        function test_does_not_mutate_input_array() {
            var original = root.sampleApplications.slice();
            launcherAppsService.allApplicationsSorted(root.sampleApplications);
            compare(root.sampleApplications.length, original.length);
            for (var i = 0; i < original.length; i++) {
                compare(root.sampleApplications[i].id, original[i].id);
            }
        }

        function test_handles_empty_list() {
            var results = launcherAppsService.allApplicationsSorted([]);
            compare(results.length, 0);
        }
    }
}
