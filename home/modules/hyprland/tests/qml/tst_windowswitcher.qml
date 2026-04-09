import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: windowSwitcher

        property bool overlayVisible: false
        property bool confirmRequestedBeforeOverlayReady: false
        property int selectedIndex: 0
        property var windowList: []
        property int submapResetDispatchCount: 0
        property string lastFocusedWindowAddress: ""

        function buildFilteredWindowListFromFreshData(freshClientsJson, focusedWorkspaceId, toplevelsMap) {
            var freshClients;
            try {
                freshClients = JSON.parse(freshClientsJson);
            } catch (error) {
                return;
            }

            var filtered = [];
            for (var i = 0; i < freshClients.length; i++) {
                var client = freshClients[i];

                if (!client.workspace || client.workspace.id !== focusedWorkspaceId)
                    continue;

                var address = client.address.replace(/^0x/, "");
                var toplevel = toplevelsMap[address];
                if (!toplevel)
                    continue;

                filtered.push({
                    address: address,
                    title: client.title || client.class || "Unknown",
                    windowClass: client.class || "",
                    focusHistoryId: client.focusHistoryID !== undefined ? client.focusHistoryID : 9999
                });
            }

            filtered.sort(function(a, b) { return a.focusHistoryId - b.focusHistoryId; });
            windowList = filtered;
        }

        function clampSelectedIndex() {
            if (windowList.length === 0)
                selectedIndex = 0;
            else if (selectedIndex >= windowList.length)
                selectedIndex = windowList.length - 1;
        }

        function selectNextWindow() {
            if (windowList.length === 0) return;
            selectedIndex = (selectedIndex + 1) % windowList.length;
        }

        function selectPreviousWindow() {
            if (windowList.length === 0) return;
            selectedIndex = (selectedIndex - 1 + windowList.length) % windowList.length;
        }

        function finishOpenSwitcher() {
            if (windowList.length === 0)
                return;

            if (confirmRequestedBeforeOverlayReady) {
                var indexToFocus = windowList.length > 1 ? 1 : 0;
                lastFocusedWindowAddress = windowList[indexToFocus].address;
                closeSwitcher();
                return;
            }

            selectedIndex = windowList.length > 1 ? 1 : 0;
            overlayVisible = true;
        }

        function confirmSelection() {
            if (!overlayVisible) {
                confirmRequestedBeforeOverlayReady = true;
                return;
            }

            clampSelectedIndex();
            if (windowList.length > 0 && selectedIndex < windowList.length)
                lastFocusedWindowAddress = windowList[selectedIndex].address;
            closeSwitcher();
        }

        function closeSwitcher() {
            overlayVisible = false;
            confirmRequestedBeforeOverlayReady = false;
            windowList = [];
            selectedIndex = 0;
            submapResetDispatchCount++;
        }

        function cancelSwitcher() {
            closeSwitcher();
        }

        function parseThemeColors(jsonText) {
            try {
                return JSON.parse(jsonText);
            } catch (error) {
                return null;
            }
        }

        function rgbStringToQtColor(rgbString, alpha) {
            var parts = rgbString.split(",");
            if (parts.length !== 3) return Qt.rgba(0, 0, 0, alpha);
            return Qt.rgba(
                parseInt(parts[0].trim()) / 255.0,
                parseInt(parts[1].trim()) / 255.0,
                parseInt(parts[2].trim()) / 255.0,
                alpha
            );
        }
    }

    property var sampleToplevelsMap: ({
        "abc123": { wayland: "wl-abc123" },
        "def456": { wayland: "wl-def456" },
        "ghi789": { wayland: "wl-ghi789" }
    })

    property string sampleClientsJson: JSON.stringify([
        { address: "0xabc123", title: "Firefox", "class": "firefox", workspace: { id: 1 }, focusHistoryID: 2 },
        { address: "0xdef456", title: "Terminal", "class": "kitty", workspace: { id: 1 }, focusHistoryID: 0 },
        { address: "0xghi789", title: "Code", "class": "code", workspace: { id: 2 }, focusHistoryID: 1 }
    ])

    TestCase {
        name: "WindowSwitcherBuildFilteredWindowList"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_filters_windows_by_workspace() {
            windowSwitcher.buildFilteredWindowListFromFreshData(
                root.sampleClientsJson, 1, root.sampleToplevelsMap
            );
            compare(windowSwitcher.windowList.length, 2);
        }

        function test_strips_hex_prefix_from_address() {
            windowSwitcher.buildFilteredWindowListFromFreshData(
                root.sampleClientsJson, 1, root.sampleToplevelsMap
            );
            compare(windowSwitcher.windowList[0].address, "def456");
        }

        function test_sorts_by_focus_history_id_ascending() {
            windowSwitcher.buildFilteredWindowListFromFreshData(
                root.sampleClientsJson, 1, root.sampleToplevelsMap
            );
            compare(windowSwitcher.windowList[0].title, "Terminal");
            compare(windowSwitcher.windowList[1].title, "Firefox");
        }

        function test_skips_clients_without_toplevel() {
            var clients = JSON.stringify([
                { address: "0xunknown", title: "Ghost", "class": "ghost", workspace: { id: 1 }, focusHistoryID: 0 }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_skips_clients_without_workspace() {
            var clients = JSON.stringify([
                { address: "0xabc123", title: "Orphan", "class": "orphan", focusHistoryID: 0 }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_uses_class_as_title_fallback() {
            var clients = JSON.stringify([
                { address: "0xabc123", title: "", "class": "fallback-class", workspace: { id: 1 }, focusHistoryID: 0 }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList[0].title, "fallback-class");
        }

        function test_uses_unknown_when_no_title_or_class() {
            var clients = JSON.stringify([
                { address: "0xabc123", title: "", "class": "", workspace: { id: 1 }, focusHistoryID: 0 }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList[0].title, "Unknown");
        }

        function test_handles_invalid_json() {
            windowSwitcher.windowList = [{ address: "existing" }];
            windowSwitcher.buildFilteredWindowListFromFreshData("not valid json", 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList.length, 1);
        }

        function test_handles_empty_clients_list() {
            windowSwitcher.buildFilteredWindowListFromFreshData("[]", 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_defaults_focus_history_id_to_9999_when_missing() {
            var clients = JSON.stringify([
                { address: "0xabc123", title: "NoHistory", "class": "app", workspace: { id: 1 } }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, root.sampleToplevelsMap);
            compare(windowSwitcher.windowList[0].focusHistoryId, 9999);
        }

        function test_preserves_window_class() {
            windowSwitcher.buildFilteredWindowListFromFreshData(
                root.sampleClientsJson, 1, root.sampleToplevelsMap
            );
            compare(windowSwitcher.windowList[0].windowClass, "kitty");
            compare(windowSwitcher.windowList[1].windowClass, "firefox");
        }
    }

    TestCase {
        name: "WindowSwitcherNavigation"

        function init() {
            windowSwitcher.windowList = [
                { address: "a", title: "Win1" },
                { address: "b", title: "Win2" },
                { address: "c", title: "Win3" }
            ];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = true;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_select_next_wraps_around() {
            windowSwitcher.selectedIndex = 2;
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 0);
        }

        function test_select_next_increments() {
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 1);
        }

        function test_select_previous_wraps_around() {
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.selectPreviousWindow();
            compare(windowSwitcher.selectedIndex, 2);
        }

        function test_select_previous_decrements() {
            windowSwitcher.selectedIndex = 2;
            windowSwitcher.selectPreviousWindow();
            compare(windowSwitcher.selectedIndex, 1);
        }

        function test_select_next_noop_on_empty_list() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 5;
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 5);
        }

        function test_select_previous_noop_on_empty_list() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 5;
            windowSwitcher.selectPreviousWindow();
            compare(windowSwitcher.selectedIndex, 5);
        }

        function test_clamp_to_last_when_index_exceeds_length() {
            windowSwitcher.selectedIndex = 10;
            windowSwitcher.clampSelectedIndex();
            compare(windowSwitcher.selectedIndex, 2);
        }

        function test_clamp_to_zero_when_list_empty() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 5;
            windowSwitcher.clampSelectedIndex();
            compare(windowSwitcher.selectedIndex, 0);
        }

        function test_clamp_preserves_valid_index() {
            windowSwitcher.selectedIndex = 1;
            windowSwitcher.clampSelectedIndex();
            compare(windowSwitcher.selectedIndex, 1);
        }

        function test_full_cycle_through_all_windows() {
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 1);
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 2);
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 0);
        }
    }

    TestCase {
        name: "WindowSwitcherFinishOpen"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_does_not_open_when_no_windows() {
            windowSwitcher.finishOpenSwitcher();
            verify(!windowSwitcher.overlayVisible);
        }

        function test_selects_second_window_when_multiple() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" },
                { address: "c", title: "W3" }
            ];
            windowSwitcher.finishOpenSwitcher();
            compare(windowSwitcher.selectedIndex, 1);
            verify(windowSwitcher.overlayVisible);
        }

        function test_selects_first_window_when_only_one() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" }
            ];
            windowSwitcher.finishOpenSwitcher();
            compare(windowSwitcher.selectedIndex, 0);
            verify(windowSwitcher.overlayVisible);
        }

        function test_handles_confirm_before_overlay_ready() {
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" }
            ];
            windowSwitcher.finishOpenSwitcher();
            verify(!windowSwitcher.overlayVisible);
            verify(!windowSwitcher.confirmRequestedBeforeOverlayReady);
            compare(windowSwitcher.windowList.length, 0);
            compare(windowSwitcher.selectedIndex, 0);
            compare(windowSwitcher.submapResetDispatchCount, 1);
            compare(windowSwitcher.lastFocusedWindowAddress, "b");
        }
    }

    TestCase {
        name: "WindowSwitcherConfirmAndCancel"

        function init() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" }
            ];
            windowSwitcher.selectedIndex = 1;
            windowSwitcher.overlayVisible = true;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_confirm_closes_overlay() {
            windowSwitcher.confirmSelection();
            verify(!windowSwitcher.overlayVisible);
        }

        function test_confirm_resets_window_list() {
            windowSwitcher.confirmSelection();
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_confirm_resets_selected_index() {
            windowSwitcher.confirmSelection();
            compare(windowSwitcher.selectedIndex, 0);
        }

        function test_confirm_when_overlay_not_visible_sets_flag() {
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmSelection();
            verify(windowSwitcher.confirmRequestedBeforeOverlayReady);
            compare(windowSwitcher.windowList.length, 2);
        }

        function test_cancel_resets_everything() {
            windowSwitcher.cancelSwitcher();
            verify(!windowSwitcher.overlayVisible);
            verify(!windowSwitcher.confirmRequestedBeforeOverlayReady);
            compare(windowSwitcher.windowList.length, 0);
            compare(windowSwitcher.selectedIndex, 0);
        }

        function test_cancel_clears_confirm_before_ready_flag() {
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;
            windowSwitcher.cancelSwitcher();
            verify(!windowSwitcher.confirmRequestedBeforeOverlayReady);
        }
    }

    TestCase {
        name: "WindowSwitcherMultipleWindowsStress"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_fifteen_windows_same_workspace() {
            var toplevels = {};
            var clients = [];
            for (var i = 0; i < 15; i++) {
                var addr = "addr" + i;
                toplevels[addr] = { wayland: "wl-" + addr };
                clients.push({
                    address: "0x" + addr,
                    title: "Window " + i,
                    "class": "app" + (i % 5),
                    workspace: { id: 1 },
                    focusHistoryID: i
                });
            }
            windowSwitcher.buildFilteredWindowListFromFreshData(
                JSON.stringify(clients), 1, toplevels
            );
            // All 15 windows shown (no deduplication in switcher)
            compare(windowSwitcher.windowList.length, 15);
            // Sorted by focusHistoryId
            compare(windowSwitcher.windowList[0].focusHistoryId, 0);
            compare(windowSwitcher.windowList[14].focusHistoryId, 14);
        }

        function test_all_windows_same_focus_id() {
            var toplevels = {
                "a": { wayland: "wl-a" },
                "b": { wayland: "wl-b" },
                "c": { wayland: "wl-c" }
            };
            var clients = JSON.stringify([
                { address: "0xa", title: "Win A", "class": "app", workspace: { id: 1 }, focusHistoryID: 5 },
                { address: "0xb", title: "Win B", "class": "app", workspace: { id: 1 }, focusHistoryID: 5 },
                { address: "0xc", title: "Win C", "class": "app", workspace: { id: 1 }, focusHistoryID: 5 }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 3);
            // All have same focusHistoryId — sort is stable, order depends on implementation
        }

        function test_no_windows_on_focused_workspace() {
            var toplevels = { "a": { wayland: "wl-a" } };
            var clients = JSON.stringify([
                { address: "0xa", title: "Win", "class": "app", workspace: { id: 2 }, focusHistoryID: 0 }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_mixed_workspaces_only_focused_shown() {
            var toplevels = {
                "a": { wayland: "wl-a" },
                "b": { wayland: "wl-b" },
                "c": { wayland: "wl-c" },
                "d": { wayland: "wl-d" }
            };
            var clients = JSON.stringify([
                { address: "0xa", title: "WS1-A", "class": "app1", workspace: { id: 1 }, focusHistoryID: 0 },
                { address: "0xb", title: "WS2-B", "class": "app2", workspace: { id: 2 }, focusHistoryID: 1 },
                { address: "0xc", title: "WS1-C", "class": "app3", workspace: { id: 1 }, focusHistoryID: 2 },
                { address: "0xd", title: "WS3-D", "class": "app4", workspace: { id: 3 }, focusHistoryID: 3 }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 2);
            compare(windowSwitcher.windowList[0].title, "WS1-A");
            compare(windowSwitcher.windowList[1].title, "WS1-C");
        }

        function test_all_windows_no_focus_history() {
            var toplevels = {
                "a": { wayland: "wl-a" },
                "b": { wayland: "wl-b" }
            };
            var clients = JSON.stringify([
                { address: "0xa", title: "Auto1", "class": "app1", workspace: { id: 1 } },
                { address: "0xb", title: "Auto2", "class": "app2", workspace: { id: 1 } }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 2);
            compare(windowSwitcher.windowList[0].focusHistoryId, 9999);
            compare(windowSwitcher.windowList[1].focusHistoryId, 9999);
        }

        function test_windows_missing_toplevels_are_filtered() {
            var toplevels = { "a": { wayland: "wl-a" } };
            var clients = JSON.stringify([
                { address: "0xa", title: "Has Toplevel", "class": "app1", workspace: { id: 1 }, focusHistoryID: 0 },
                { address: "0xb", title: "No Toplevel", "class": "app2", workspace: { id: 1 }, focusHistoryID: 1 },
                { address: "0xc", title: "Also No", "class": "app3", workspace: { id: 1 }, focusHistoryID: 2 }
            ]);
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            compare(windowSwitcher.windowList.length, 1);
            compare(windowSwitcher.windowList[0].title, "Has Toplevel");
        }
    }

    TestCase {
        name: "WindowSwitcherStateMachineEdgeCases"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_double_confirm_when_overlay_hidden() {
            // Confirm twice before overlay opens — flag set once, second is noop (flag already true)
            windowSwitcher.confirmSelection();
            verify(windowSwitcher.confirmRequestedBeforeOverlayReady);
            windowSwitcher.confirmSelection();
            verify(windowSwitcher.confirmRequestedBeforeOverlayReady);
        }

        function test_confirm_after_cancel_sets_flag() {
            windowSwitcher.windowList = [{ address: "a", title: "W1" }];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.cancelSwitcher();
            // Now overlay is hidden, confirm should set the pre-ready flag
            windowSwitcher.confirmSelection();
            verify(windowSwitcher.confirmRequestedBeforeOverlayReady);
        }

        function test_nav_on_single_window_stays_at_zero() {
            windowSwitcher.windowList = [{ address: "a", title: "W1" }];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 0);
            windowSwitcher.selectPreviousWindow();
            compare(windowSwitcher.selectedIndex, 0);
        }

        function test_nav_on_two_windows_toggles() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" }
            ];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 1);
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 0);
            windowSwitcher.selectPreviousWindow();
            compare(windowSwitcher.selectedIndex, 1);
        }

        function test_finish_open_with_confirm_before_ready_and_single_window() {
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;
            windowSwitcher.windowList = [{ address: "a", title: "W1" }];
            windowSwitcher.finishOpenSwitcher();
            verify(!windowSwitcher.overlayVisible);
            verify(!windowSwitcher.confirmRequestedBeforeOverlayReady);
            compare(windowSwitcher.windowList.length, 0);
            compare(windowSwitcher.submapResetDispatchCount, 1);
            compare(windowSwitcher.lastFocusedWindowAddress, "a");
        }

        function test_finish_open_empty_list_with_confirm_before_ready() {
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;
            windowSwitcher.finishOpenSwitcher();
            // Empty list — early return, flag NOT cleared
            verify(windowSwitcher.confirmRequestedBeforeOverlayReady);
            verify(!windowSwitcher.overlayVisible);
        }

        function test_rapid_next_next_next_confirm_cycle() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" },
                { address: "c", title: "W3" },
                { address: "d", title: "W4" },
                { address: "e", title: "W5" }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.selectedIndex = 1;

            // Rapid cycling: 10 nexts
            for (var i = 0; i < 10; i++) {
                windowSwitcher.selectNextWindow();
            }
            // 1 + 10 = 11, 11 % 5 = 1
            compare(windowSwitcher.selectedIndex, 1);

            windowSwitcher.confirmSelection();
            verify(!windowSwitcher.overlayVisible);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_clamp_handles_window_list_shrink() {
            // Simulate: overlay open with 5 windows, user selected index 4
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" },
                { address: "c", title: "W3" },
                { address: "d", title: "W4" },
                { address: "e", title: "W5" }
            ];
            windowSwitcher.selectedIndex = 4;
            windowSwitcher.overlayVisible = true;

            // Windows shrink (e.g., 3 closed between overlay open and confirm)
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" }
            ];
            // Confirm should clamp
            windowSwitcher.confirmSelection();
            // selectedIndex was 4, clamped to 1 (length-1), then reset to 0 after confirm
            compare(windowSwitcher.selectedIndex, 0);
        }

        function test_open_cancel_open_confirm_sequence() {
            var toplevels = {
                "a": { wayland: "wl-a" },
                "b": { wayland: "wl-b" }
            };
            var clients = JSON.stringify([
                { address: "0xa", title: "Win A", "class": "app1", workspace: { id: 1 }, focusHistoryID: 0 },
                { address: "0xb", title: "Win B", "class": "app2", workspace: { id: 1 }, focusHistoryID: 1 }
            ]);

            // Open
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);
            compare(windowSwitcher.selectedIndex, 1);

            // Cancel
            windowSwitcher.cancelSwitcher();
            verify(!windowSwitcher.overlayVisible);
            compare(windowSwitcher.windowList.length, 0);

            // Open again
            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);
            compare(windowSwitcher.selectedIndex, 1);

            // Confirm
            windowSwitcher.confirmSelection();
            verify(!windowSwitcher.overlayVisible);
        }
    }

    TestCase {
        name: "WindowSwitcherLargeWindowList"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_thirty_windows_navigation() {
            var windows = [];
            for (var i = 0; i < 30; i++) {
                windows.push({ address: "addr" + i, title: "Window " + i });
            }
            windowSwitcher.windowList = windows;
            windowSwitcher.overlayVisible = true;
            windowSwitcher.selectedIndex = 0;

            // Navigate forward through all 30
            for (var j = 0; j < 30; j++) {
                compare(windowSwitcher.selectedIndex, j);
                windowSwitcher.selectNextWindow();
            }
            // Wrapped back to 0
            compare(windowSwitcher.selectedIndex, 0);

            // Navigate backward through all 30
            for (var k = 0; k < 30; k++) {
                windowSwitcher.selectPreviousWindow();
            }
            compare(windowSwitcher.selectedIndex, 0);
        }

        function test_thirty_windows_build_and_sort() {
            var toplevels = {};
            var clients = [];
            for (var i = 0; i < 30; i++) {
                var addr = "win" + i;
                toplevels[addr] = { wayland: "wl-" + addr };
                clients.push({
                    address: "0x" + addr,
                    title: "App " + i,
                    "class": "app" + i,
                    workspace: { id: 1 },
                    focusHistoryID: 29 - i // Reverse order
                });
            }
            windowSwitcher.buildFilteredWindowListFromFreshData(
                JSON.stringify(clients), 1, toplevels
            );
            compare(windowSwitcher.windowList.length, 30);
            // Should be sorted: focusHistoryId 0 first (which is app29)
            compare(windowSwitcher.windowList[0].title, "App 29");
            compare(windowSwitcher.windowList[0].focusHistoryId, 0);
            compare(windowSwitcher.windowList[29].title, "App 0");
            compare(windowSwitcher.windowList[29].focusHistoryId, 29);
        }
    }

    TestCase {
        name: "WindowSwitcherSubmapResetOnClose"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_confirm_dispatches_submap_reset_and_focuses_selected() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.selectedIndex = 1;

            windowSwitcher.confirmSelection();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            compare(windowSwitcher.lastFocusedWindowAddress, "b");
        }

        function test_cancel_dispatches_submap_reset() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" }
            ];
            windowSwitcher.overlayVisible = true;

            windowSwitcher.cancelSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 1);
        }

        function test_card_click_then_confirm_dispatches_submap_reset() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.selectedIndex = 0;

            windowSwitcher.confirmSelection();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            verify(!windowSwitcher.overlayVisible);
            compare(windowSwitcher.windowList.length, 0);
        }

        function test_quick_switch_dispatches_submap_reset_and_focuses_window() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" }
            ];
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;

            windowSwitcher.finishOpenSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            verify(!windowSwitcher.overlayVisible);
            compare(windowSwitcher.lastFocusedWindowAddress, "b");
        }

        function test_close_switcher_resets_all_state() {
            windowSwitcher.windowList = [
                { address: "a", title: "W1" },
                { address: "b", title: "W2" }
            ];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.selectedIndex = 1;
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;

            windowSwitcher.closeSwitcher();

            verify(!windowSwitcher.overlayVisible);
            verify(!windowSwitcher.confirmRequestedBeforeOverlayReady);
            compare(windowSwitcher.windowList.length, 0);
            compare(windowSwitcher.selectedIndex, 0);
            compare(windowSwitcher.submapResetDispatchCount, 1);
        }

        function test_submap_desync_scenario_card_click_then_reopen() {
            var toplevels = {
                "a": { wayland: "wl-a" },
                "b": { wayland: "wl-b" }
            };
            var clients = JSON.stringify([
                { address: "0xa", title: "Win A", "class": "app1", workspace: { id: 1 }, focusHistoryID: 0 },
                { address: "0xb", title: "Win B", "class": "app2", workspace: { id: 1 }, focusHistoryID: 1 }
            ]);

            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);

            windowSwitcher.selectedIndex = 0;
            windowSwitcher.confirmSelection();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            verify(!windowSwitcher.overlayVisible);
            compare(windowSwitcher.windowList.length, 0);

            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);
            compare(windowSwitcher.selectedIndex, 1);
        }

        function test_submap_desync_scenario_click_outside_then_reopen() {
            var toplevels = {
                "a": { wayland: "wl-a" },
                "b": { wayland: "wl-b" }
            };
            var clients = JSON.stringify([
                { address: "0xa", title: "Win A", "class": "app1", workspace: { id: 1 }, focusHistoryID: 0 },
                { address: "0xb", title: "Win B", "class": "app2", workspace: { id: 1 }, focusHistoryID: 1 }
            ]);

            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);

            windowSwitcher.cancelSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 1);
            verify(!windowSwitcher.overlayVisible);

            windowSwitcher.buildFilteredWindowListFromFreshData(clients, 1, toplevels);
            windowSwitcher.finishOpenSwitcher();
            verify(windowSwitcher.overlayVisible);
            compare(windowSwitcher.selectedIndex, 1);
        }

        function test_multiple_close_cycles_dispatch_each_time() {
            windowSwitcher.windowList = [{ address: "a", title: "W1" }];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.cancelSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 1);

            windowSwitcher.windowList = [{ address: "b", title: "W2" }];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.confirmSelection();
            compare(windowSwitcher.submapResetDispatchCount, 2);

            windowSwitcher.windowList = [{ address: "c", title: "W3" }];
            windowSwitcher.overlayVisible = true;
            windowSwitcher.cancelSwitcher();
            compare(windowSwitcher.submapResetDispatchCount, 3);
        }
    }

    TestCase {
        name: "WindowSwitcherThemeColors"

        function init() {
            windowSwitcher.windowList = [];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.overlayVisible = false;
            windowSwitcher.confirmRequestedBeforeOverlayReady = false;
            windowSwitcher.submapResetDispatchCount = 0;
            windowSwitcher.lastFocusedWindowAddress = "";
        }

        function test_parse_valid_theme_colors() {
            var json = '{"backgroundRgb": "26, 27, 38", "foreground": "#c0caf5", "accent": "#7aa2f7"}';
            var result = windowSwitcher.parseThemeColors(json);
            verify(result !== null);
            compare(result.backgroundRgb, "26, 27, 38");
        }

        function test_parse_invalid_theme_returns_null() {
            compare(windowSwitcher.parseThemeColors("not json"), null);
        }

        function test_rgb_string_to_color_valid() {
            var c = windowSwitcher.rgbStringToQtColor("255, 128, 0", 0.5);
            verify(Math.abs(c.r - 1.0) < 0.01);
            verify(Math.abs(c.g - 0.502) < 0.01);
            verify(Math.abs(c.b - 0.0) < 0.01);
            verify(Math.abs(c.a - 0.5) < 0.01);
        }

        function test_rgb_string_invalid_returns_black() {
            var c = windowSwitcher.rgbStringToQtColor("invalid", 0.85);
            compare(c.r, 0);
            compare(c.g, 0);
            compare(c.b, 0);
            verify(Math.abs(c.a - 0.85) < 0.01);
        }
    }
}
