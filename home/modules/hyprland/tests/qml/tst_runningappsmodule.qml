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
}
