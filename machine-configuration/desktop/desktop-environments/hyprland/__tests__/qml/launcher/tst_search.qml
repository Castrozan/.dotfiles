import QtQuick
import QtTest

LauncherApplicationsFixture {
    id: root

    TestCase {
        name: "LauncherAppsServiceSearch"

        function init() {
            launcherAppsService.usageHistoryByAppId = {};
        }

        function test_search_matches_by_name() {
            var results = launcherAppsService.search("fire", root.sampleApplications);
            compare(results.length, 1);
            compare(results[0].id, "firefox");
        }

        function test_search_is_case_insensitive() {
            var results = launcherAppsService.search("FIREFOX", root.sampleApplications);
            compare(results.length, 1);
            compare(results[0].id, "firefox");
        }

        function test_search_matches_by_generic_name() {
            var results = launcherAppsService.search("web browser", root.sampleApplications);
            compare(results.length, 2);
        }

        function test_search_matches_by_comment() {
            var results = launcherAppsService.search("GPU accelerated", root.sampleApplications);
            compare(results.length, 1);
            compare(results[0].id, "kitty");
        }

        function test_search_matches_by_keywords() {
            var results = launcherAppsService.search("vscode", root.sampleApplications);
            compare(results.length, 1);
            compare(results[0].id, "code");
        }

        function test_search_returns_empty_for_no_match() {
            var results = launcherAppsService.search("zzzznonexistent", root.sampleApplications);
            compare(results.length, 0);
        }

        function test_search_returns_empty_for_empty_apps_list() {
            var results = launcherAppsService.search("fire", []);
            compare(results.length, 0);
        }

        function test_search_prioritizes_name_starts_with_over_contains() {
            var apps = [
                {
                    id: "app1",
                    name: "Thunderbird Firefox",
                    genericName: "",
                    comment: "",
                    keywords: []
                },
                {
                    id: "app2",
                    name: "Firefox",
                    genericName: "",
                    comment: "",
                    keywords: []
                }
            ];
            var results = launcherAppsService.search("fire", apps);
            compare(results.length, 2);
            compare(results[0].id, "app2");
        }

        function test_search_sorts_by_usage_history_within_same_prefix_group() {
            launcherAppsService.usageHistoryByAppId = {
                "chromium": 2000,
                "firefox": 1000
            };
            var results = launcherAppsService.search("browser", root.sampleApplications);
            compare(results.length, 2);
            compare(results[0].id, "chromium");
            compare(results[1].id, "firefox");
        }

        function test_search_falls_back_to_alphabetical_when_no_usage() {
            var results = launcherAppsService.search("browser", root.sampleApplications);
            compare(results.length, 2);
            compare(results[0].id, "chromium");
            compare(results[1].id, "firefox");
        }

        function test_search_empty_query_matches_all() {
            var results = launcherAppsService.search("", root.sampleApplications);
            compare(results.length, 5);
        }

        function test_search_partial_keyword_match() {
            var results = launcherAppsService.search("inter", root.sampleApplications);
            compare(results.length, 2);
        }
    }
}
