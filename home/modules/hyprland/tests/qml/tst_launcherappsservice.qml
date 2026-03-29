import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: launcherAppsService

        property var usageHistoryByAppId: ({})

        function search(queryText, allApplications) {
            var results = [];
            var lowerQuery = queryText.toLowerCase();

            for (var i = 0; i < allApplications.length; i++) {
                var entry = allApplications[i];
                var nameMatch = entry.name.toLowerCase().includes(lowerQuery);
                var genericNameMatch = entry.genericName && entry.genericName.toLowerCase().includes(lowerQuery);
                var commentMatch = entry.comment && entry.comment.toLowerCase().includes(lowerQuery);
                var keywordsMatch = false;

                if (!nameMatch && !genericNameMatch && !commentMatch) {
                    for (var j = 0; j < entry.keywords.length; j++) {
                        if (entry.keywords[j].toLowerCase().includes(lowerQuery)) {
                            keywordsMatch = true;
                            break;
                        }
                    }
                }

                if (nameMatch || genericNameMatch || commentMatch || keywordsMatch) {
                    results.push(entry);
                }
            }

            results.sort(function(entryA, entryB) {
                var aStartsWith = entryA.name.toLowerCase().startsWith(lowerQuery);
                var bStartsWith = entryB.name.toLowerCase().startsWith(lowerQuery);
                if (aStartsWith && !bStartsWith) return -1;
                if (!aStartsWith && bStartsWith) return 1;

                var aLastUsedTimestamp = usageHistoryByAppId[entryA.id] || 0;
                var bLastUsedTimestamp = usageHistoryByAppId[entryB.id] || 0;
                if (aLastUsedTimestamp !== bLastUsedTimestamp)
                    return bLastUsedTimestamp - aLastUsedTimestamp;

                return entryA.name.localeCompare(entryB.name);
            });

            return results;
        }

        function allApplicationsSorted(allApplications) {
            var sorted = allApplications.slice();
            sorted.sort(function(entryA, entryB) {
                var aLastUsedTimestamp = usageHistoryByAppId[entryA.id] || 0;
                var bLastUsedTimestamp = usageHistoryByAppId[entryB.id] || 0;
                if (aLastUsedTimestamp !== bLastUsedTimestamp)
                    return bLastUsedTimestamp - aLastUsedTimestamp;
                return entryA.name.localeCompare(entryB.name);
            });
            return sorted;
        }

        function parseLoadedUsageHistory(rawJsonText) {
            try {
                var parsed = JSON.parse(rawJsonText.trim());
                if (parsed && typeof parsed === "object") {
                    usageHistoryByAppId = parsed;
                    return true;
                }
            } catch (parseError) {
                usageHistoryByAppId = {};
            }
            return false;
        }
    }

    property var sampleApplications: [
        { id: "firefox", name: "Firefox", genericName: "Web Browser", comment: "Browse the web", keywords: ["internet", "www"] },
        { id: "chromium", name: "Chromium", genericName: "Web Browser", comment: "", keywords: ["internet", "chrome"] },
        { id: "kitty", name: "Kitty", genericName: "Terminal Emulator", comment: "GPU accelerated terminal", keywords: ["shell", "console"] },
        { id: "nautilus", name: "Files", genericName: "File Manager", comment: "Access and organize files", keywords: ["folder", "directory"] },
        { id: "code", name: "Visual Studio Code", genericName: "Text Editor", comment: "Code editing", keywords: ["vscode", "editor"] }
    ]

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
                { id: "app1", name: "Thunderbird Firefox", genericName: "", comment: "", keywords: [] },
                { id: "app2", name: "Firefox", genericName: "", comment: "", keywords: [] }
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
            launcherAppsService.usageHistoryByAppId = {"existing": 1};
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
