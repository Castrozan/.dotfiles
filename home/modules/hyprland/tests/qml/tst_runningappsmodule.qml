import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: runningAppsModule

        property var runningAppsByClass: []
        property string focusedWindowClass: ""
        property var firstSeenOrderByClass: ({})
        property int firstSeenOrderNextIndex: 0

        readonly property var windowClassToIconName: ({
            "chrome-global": "google-chrome",
            "code": "vscode",
            "code - insiders": "vscode-insiders",
            "cursor": "cursor"
        })

        function resolveIconName(windowClass) {
            var lowerClass = windowClass.toLowerCase();
            var mapped = windowClassToIconName[lowerClass];
            return mapped !== undefined ? mapped : lowerClass;
        }

        function parseClientsAndRebuildAppList(clientsJson) {
            var clients;
            try {
                clients = JSON.parse(clientsJson);
            } catch (error) {
                return;
            }

            var mostRecentWindowByClass = {};
            var detectedFocusedClass = "";

            for (var i = 0; i < clients.length; i++) {
                var client = clients[i];
                var windowClass = client["class"] || "";
                if (windowClass === "")
                    continue;

                if (client.focusHistoryID === 0)
                    detectedFocusedClass = windowClass;

                var existing = mostRecentWindowByClass[windowClass];
                var clientFocusId = client.focusHistoryID !== undefined ? client.focusHistoryID : 9999;
                if (!existing || (clientFocusId < existing.focusHistoryID)) {
                    mostRecentWindowByClass[windowClass] = {
                        windowClass: windowClass,
                        address: client.address,
                        focusHistoryID: clientFocusId
                    };
                }
            }

            var updatedFirstSeenOrder = {};
            for (var key in firstSeenOrderByClass) {
                updatedFirstSeenOrder[key] = firstSeenOrderByClass[key];
            }
            var updatedNextIndex = firstSeenOrderNextIndex;

            for (var cls in mostRecentWindowByClass) {
                if (updatedFirstSeenOrder[cls] === undefined) {
                    updatedFirstSeenOrder[cls] = updatedNextIndex;
                    updatedNextIndex++;
                }
            }

            for (var cls2 in updatedFirstSeenOrder) {
                if (!mostRecentWindowByClass[cls2])
                    delete updatedFirstSeenOrder[cls2];
            }

            firstSeenOrderByClass = updatedFirstSeenOrder;
            firstSeenOrderNextIndex = updatedNextIndex;

            var sortedAppList = [];
            for (var cls3 in mostRecentWindowByClass)
                sortedAppList.push(mostRecentWindowByClass[cls3]);

            sortedAppList.sort(function(a, b) {
                return firstSeenOrderByClass[a.windowClass] - firstSeenOrderByClass[b.windowClass];
            });

            runningAppsByClass = sortedAppList;
            focusedWindowClass = detectedFocusedClass;
        }
    }

    TestCase {
        name: "RunningAppsModuleResolveIconName"

        function test_maps_chrome_global_to_google_chrome() {
            compare(runningAppsModule.resolveIconName("chrome-global"), "google-chrome");
        }

        function test_maps_code_to_vscode() {
            compare(runningAppsModule.resolveIconName("code"), "vscode");
        }

        function test_maps_code_insiders_to_vscode_insiders() {
            compare(runningAppsModule.resolveIconName("Code - Insiders"), "vscode-insiders");
        }

        function test_maps_cursor_to_cursor() {
            compare(runningAppsModule.resolveIconName("Cursor"), "cursor");
        }

        function test_unmapped_class_returns_lowercase() {
            compare(runningAppsModule.resolveIconName("Firefox"), "firefox");
        }

        function test_already_lowercase_unmapped_passes_through() {
            compare(runningAppsModule.resolveIconName("kitty"), "kitty");
        }

        function test_empty_string_returns_empty() {
            compare(runningAppsModule.resolveIconName(""), "");
        }
    }

    TestCase {
        name: "RunningAppsModuleDeduplication"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_deduplicates_same_class_windows() {
            var clients = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 2 },
                { address: "0x2", "class": "firefox", focusHistoryID: 0 },
                { address: "0x3", "class": "kitty", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 2);
        }

        function test_keeps_most_recently_focused_window_per_class() {
            var clients = JSON.stringify([
                { address: "0xold", "class": "firefox", focusHistoryID: 5 },
                { address: "0xnew", "class": "firefox", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass[0].address, "0xnew");
        }

        function test_skips_clients_with_empty_class() {
            var clients = JSON.stringify([
                { address: "0x1", "class": "", focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "kitty");
        }

        function test_skips_clients_without_class() {
            var clients = JSON.stringify([
                { address: "0x1", focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
        }

        function test_defaults_focus_history_to_9999_when_missing() {
            var clients = JSON.stringify([
                { address: "0x1", "class": "firefox" },
                { address: "0x2", "class": "firefox", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass[0].address, "0x2");
        }
    }

    TestCase {
        name: "RunningAppsModuleFocusDetection"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_detects_focused_window_class() {
            var clients = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 1 },
                { address: "0x2", "class": "kitty", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.focusedWindowClass, "kitty");
        }

        function test_no_focused_window_when_no_zero_history() {
            var clients = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 1 },
                { address: "0x2", "class": "kitty", focusHistoryID: 2 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.focusedWindowClass, "");
        }

        function test_empty_clients_clears_focused_class() {
            runningAppsModule.focusedWindowClass = "old";
            runningAppsModule.parseClientsAndRebuildAppList("[]");
            compare(runningAppsModule.focusedWindowClass, "");
        }
    }

    TestCase {
        name: "RunningAppsModuleFirstSeenOrdering"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_preserves_first_seen_order_across_updates() {
            var firstBatch = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(firstBatch);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "firefox");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "kitty");

            var secondBatch = JSON.stringify([
                { address: "0x2", "class": "kitty", focusHistoryID: 0 },
                { address: "0x1", "class": "firefox", focusHistoryID: 1 },
                { address: "0x3", "class": "code", focusHistoryID: 2 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(secondBatch);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "firefox");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass[2].windowClass, "code");
        }

        function test_removes_closed_apps_from_first_seen_order() {
            var firstBatch = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 1 },
                { address: "0x3", "class": "code", focusHistoryID: 2 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(firstBatch);

            var secondBatch = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 0 },
                { address: "0x3", "class": "code", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(secondBatch);
            compare(runningAppsModule.runningAppsByClass.length, 2);
            compare(runningAppsModule.firstSeenOrderByClass["kitty"], undefined);
        }

        function test_new_app_gets_next_index() {
            var firstBatch = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(firstBatch);
            compare(runningAppsModule.firstSeenOrderByClass["firefox"], 0);
            compare(runningAppsModule.firstSeenOrderNextIndex, 1);

            var secondBatch = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 1 },
                { address: "0x2", "class": "kitty", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(secondBatch);
            compare(runningAppsModule.firstSeenOrderByClass["kitty"], 1);
            compare(runningAppsModule.firstSeenOrderNextIndex, 2);
        }
    }

    TestCase {
        name: "RunningAppsModuleErrorHandling"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_invalid_json_does_not_change_state() {
            runningAppsModule.runningAppsByClass = [{ windowClass: "existing" }];
            runningAppsModule.parseClientsAndRebuildAppList("not valid json");
            compare(runningAppsModule.runningAppsByClass.length, 1);
        }

        function test_empty_clients_produces_empty_list() {
            runningAppsModule.parseClientsAndRebuildAppList("[]");
            compare(runningAppsModule.runningAppsByClass.length, 0);
        }
    }

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
                { address: "0x1", "class": "firefox", focusHistoryID: 4 },
                { address: "0x2", "class": "firefox", focusHistoryID: 2 },
                { address: "0x3", "class": "firefox", focusHistoryID: 0 },
                { address: "0x4", "class": "firefox", focusHistoryID: 3 },
                { address: "0x5", "class": "firefox", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            compare(runningAppsModule.runningAppsByClass[0].address, "0x3");
            compare(runningAppsModule.runningAppsByClass[0].focusHistoryID, 0);
        }

        function test_ten_windows_across_three_classes() {
            var clients = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 5 },
                { address: "0x2", "class": "firefox", focusHistoryID: 2 },
                { address: "0x3", "class": "firefox", focusHistoryID: 8 },
                { address: "0x4", "class": "kitty", focusHistoryID: 0 },
                { address: "0x5", "class": "kitty", focusHistoryID: 3 },
                { address: "0x6", "class": "kitty", focusHistoryID: 7 },
                { address: "0x7", "class": "kitty", focusHistoryID: 9 },
                { address: "0x8", "class": "code", focusHistoryID: 1 },
                { address: "0x9", "class": "code", focusHistoryID: 4 },
                { address: "0xa", "class": "code", focusHistoryID: 6 }
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
                { address: "0x1", "class": "firefox", focusHistoryID: 5 },
                { address: "0x2", "class": "firefox", focusHistoryID: 5 },
                { address: "0x3", "class": "firefox", focusHistoryID: 5 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            // First encountered wins when all equal (< is strict, so no replacement)
            compare(runningAppsModule.runningAppsByClass[0].address, "0x1");
        }

        function test_clicking_bar_focuses_most_recent_window_not_first() {
            // Simulates: 3 chrome windows, most recently focused is 0x2
            var clients = JSON.stringify([
                { address: "0xold", "class": "chrome-global", focusHistoryID: 10 },
                { address: "0xrecent", "class": "chrome-global", focusHistoryID: 1 },
                { address: "0xolder", "class": "chrome-global", focusHistoryID: 5 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            // Bar stores the address of the most recently focused window
            compare(runningAppsModule.runningAppsByClass[0].address, "0xrecent");
        }
    }

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
                { address: "0x1", "class": "firefox" },
                { address: "0x2", "class": "kitty" },
                { address: "0x3", "class": "code" }
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
                { address: "0x1", "class": "firefox" },
                { address: "0x2", "class": "kitty" },
                { address: "0x3", "class": "code" }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.focusedWindowClass, "");

            // Second batch: user clicked kitty
            var batch2 = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 1 },
                { address: "0x2", "class": "kitty", focusHistoryID: 0 },
                { address: "0x3", "class": "code", focusHistoryID: 2 }
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
                { address: "0x1", "class": "firefox" },
                { address: "0x2", "class": "firefox", focusHistoryID: 0 },
                { address: "0x3", "class": "firefox" }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            compare(runningAppsModule.runningAppsByClass[0].address, "0x2");
            compare(runningAppsModule.focusedWindowClass, "firefox");
        }
    }

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
                { address: "0x1", "class": "firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            // Last one encountered wins for focusedWindowClass
            compare(runningAppsModule.focusedWindowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass.length, 2);
        }

        function test_multiple_focus_id_zero_same_class() {
            var clients = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "firefox", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            // First wins (0 < 0 is false, so no replacement)
            compare(runningAppsModule.runningAppsByClass[0].address, "0x1");
            compare(runningAppsModule.focusedWindowClass, "firefox");
        }

        function test_focus_switches_between_updates() {
            var batch1 = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.focusedWindowClass, "firefox");

            var batch2 = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 1 },
                { address: "0x2", "class": "kitty", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            compare(runningAppsModule.focusedWindowClass, "kitty");
            // Order unchanged
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "firefox");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "kitty");
        }
    }

    TestCase {
        name: "RunningAppsModuleRapidLifecycle"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_app_close_and_reopen_gets_new_position() {
            // firefox opened first
            var batch1 = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.firstSeenOrderByClass["firefox"], 0);
            compare(runningAppsModule.firstSeenOrderByClass["kitty"], 1);

            // firefox closed
            var batch2 = JSON.stringify([
                { address: "0x2", "class": "kitty", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            verify(runningAppsModule.firstSeenOrderByClass["firefox"] === undefined);

            // firefox reopened — should be AFTER kitty now
            var batch3 = JSON.stringify([
                { address: "0x2", "class": "kitty", focusHistoryID: 1 },
                { address: "0x3", "class": "firefox", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch3);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "firefox");
        }

        function test_rapid_open_close_ten_cycles() {
            // Simulate 10 cycles of apps appearing and disappearing
            for (var cycle = 0; cycle < 10; cycle++) {
                var clients = [];
                // Each cycle has a different set of 3 apps from a pool of 5
                var allClasses = ["firefox", "kitty", "code", "chrome-global", "slack"];
                for (var j = 0; j < 3; j++) {
                    var idx = (cycle + j) % 5;
                    clients.push({
                        address: "0x" + (cycle * 10 + j),
                        "class": allClasses[idx],
                        focusHistoryID: j
                    });
                }
                runningAppsModule.parseClientsAndRebuildAppList(JSON.stringify(clients));
                compare(runningAppsModule.runningAppsByClass.length, 3);
            }
            // After all cycles, state should be consistent
            verify(runningAppsModule.firstSeenOrderNextIndex > 0);
            // Exactly 3 entries in firstSeenOrder (matching current 3 apps)
            var orderCount = 0;
            for (var k in runningAppsModule.firstSeenOrderByClass) orderCount++;
            compare(orderCount, 3);
        }

        function test_all_apps_close_then_reopen() {
            var batch1 = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.runningAppsByClass.length, 2);

            // All close
            runningAppsModule.parseClientsAndRebuildAppList("[]");
            compare(runningAppsModule.runningAppsByClass.length, 0);
            compare(runningAppsModule.focusedWindowClass, "");

            // Reopen in different order
            var batch2 = JSON.stringify([
                { address: "0x3", "class": "kitty", focusHistoryID: 0 },
                { address: "0x4", "class": "firefox", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            // New first-seen order: kitty first now
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "firefox");
        }

        function test_firstseenorder_index_grows_monotonically() {
            var batch1 = JSON.stringify([
                { address: "0x1", "class": "a", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.firstSeenOrderNextIndex, 1);

            // Close a, open b
            var batch2 = JSON.stringify([
                { address: "0x2", "class": "b", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            compare(runningAppsModule.firstSeenOrderNextIndex, 2);

            // Close b, open c
            var batch3 = JSON.stringify([
                { address: "0x3", "class": "c", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch3);
            compare(runningAppsModule.firstSeenOrderNextIndex, 3);

            // Index never resets, always grows
            // After 1000 cycles this would be 1000 — acceptable for a session
        }
    }

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
                { address: "0x1", "class": " ", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, " ");
        }

        function test_class_with_special_characters() {
            var clients = JSON.stringify([
                { address: "0x1", "class": "org.mozilla.firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "com.google.Chrome", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 2);
        }

        function test_case_sensitive_classes_are_separate() {
            // "Firefox" and "firefox" are different classes
            var clients = JSON.stringify([
                { address: "0x1", "class": "Firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "firefox", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 2);
        }

        function test_null_class_treated_as_empty() {
            var clients = JSON.stringify([
                { address: "0x1", "class": null, focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 1 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(clients);
            compare(runningAppsModule.runningAppsByClass.length, 1);
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "kitty");
        }
    }

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

    TestCase {
        name: "RunningAppsModuleSequentialUpdatesConsistency"

        function init() {
            runningAppsModule.runningAppsByClass = [];
            runningAppsModule.focusedWindowClass = "";
            runningAppsModule.firstSeenOrderByClass = {};
            runningAppsModule.firstSeenOrderNextIndex = 0;
        }

        function test_repeated_identical_updates_idempotent() {
            var clients = JSON.stringify([
                { address: "0x1", "class": "firefox", focusHistoryID: 0 },
                { address: "0x2", "class": "kitty", focusHistoryID: 1 }
            ]);
            // Parse same data 5 times
            for (var i = 0; i < 5; i++) {
                runningAppsModule.parseClientsAndRebuildAppList(clients);
            }
            compare(runningAppsModule.runningAppsByClass.length, 2);
            compare(runningAppsModule.focusedWindowClass, "firefox");
            compare(runningAppsModule.firstSeenOrderByClass["firefox"], 0);
            compare(runningAppsModule.firstSeenOrderByClass["kitty"], 1);
            // Index should still be 2 (not incremented on re-seen)
            compare(runningAppsModule.firstSeenOrderNextIndex, 2);
        }

        function test_address_changes_for_same_class_across_updates() {
            // Simulate window being replaced (close + open between refreshes)
            var batch1 = JSON.stringify([
                { address: "0xold", "class": "firefox", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch1);
            compare(runningAppsModule.runningAppsByClass[0].address, "0xold");

            var batch2 = JSON.stringify([
                { address: "0xnew", "class": "firefox", focusHistoryID: 0 }
            ]);
            runningAppsModule.parseClientsAndRebuildAppList(batch2);
            compare(runningAppsModule.runningAppsByClass[0].address, "0xnew");
            // Same first-seen index
            compare(runningAppsModule.firstSeenOrderByClass["firefox"], 0);
            compare(runningAppsModule.firstSeenOrderNextIndex, 1);
        }

        function test_gradual_buildup_from_empty() {
            // Simulate boot: windows appear one by one
            var classes = ["firefox", "kitty", "code", "slack", "chrome-global"];
            for (var i = 0; i < classes.length; i++) {
                var clients = [];
                for (var j = 0; j <= i; j++) {
                    clients.push({
                        address: "0x" + j,
                        "class": classes[j],
                        focusHistoryID: i - j
                    });
                }
                runningAppsModule.parseClientsAndRebuildAppList(JSON.stringify(clients));
                compare(runningAppsModule.runningAppsByClass.length, i + 1);
            }
            // Final order should be stable first-seen: firefox, kitty, code, slack, chrome-global
            compare(runningAppsModule.runningAppsByClass[0].windowClass, "firefox");
            compare(runningAppsModule.runningAppsByClass[1].windowClass, "kitty");
            compare(runningAppsModule.runningAppsByClass[2].windowClass, "code");
            compare(runningAppsModule.runningAppsByClass[3].windowClass, "slack");
            compare(runningAppsModule.runningAppsByClass[4].windowClass, "chrome-global");
        }
    }
}
