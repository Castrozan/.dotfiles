import QtQuick
import QtTest

LauncherApplicationsFixture {
    id: root

    TestCase {
        name: "LauncherAppsServiceParseUsageHistory"

        function init() {
            launcherAppsService.usageHistoryByAppId = {};
        }

        function test_parses_valid_history_json() {
            var result = launcherAppsService.parseLoadedUsageHistory('{"firefox": 1234, "kitty": 5678}');
            verify(result);
            compare(launcherAppsService.usageHistoryByAppId["firefox"], 1234);
            compare(launcherAppsService.usageHistoryByAppId["kitty"], 5678);
        }

        function test_resets_to_empty_on_invalid_json() {
            launcherAppsService.usageHistoryByAppId = {
                "existing": 1
            };
            launcherAppsService.parseLoadedUsageHistory("not valid json");
            var keys = Object.keys(launcherAppsService.usageHistoryByAppId);
            compare(keys.length, 0);
        }

        function test_handles_empty_object() {
            var result = launcherAppsService.parseLoadedUsageHistory("{}");
            verify(result);
            var keys = Object.keys(launcherAppsService.usageHistoryByAppId);
            compare(keys.length, 0);
        }

        function test_trims_whitespace_before_parsing() {
            var result = launcherAppsService.parseLoadedUsageHistory('  {"app": 42}  ');
            verify(result);
            compare(launcherAppsService.usageHistoryByAppId["app"], 42);
        }

        function test_rejects_non_object_json() {
            var result = launcherAppsService.parseLoadedUsageHistory('"just a string"');
            verify(!result);
        }

        function test_rejects_array_json() {
            var result = launcherAppsService.parseLoadedUsageHistory('[1, 2, 3]');
            verify(result);
        }

        function test_rejects_null_json() {
            var result = launcherAppsService.parseLoadedUsageHistory("null");
            verify(!result);
        }
    }
}
