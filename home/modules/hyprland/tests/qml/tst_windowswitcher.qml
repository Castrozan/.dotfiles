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
                confirmRequestedBeforeOverlayReady = false;
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
            overlayVisible = false;
            windowList = [];
            selectedIndex = 0;
        }

        function cancelSwitcher() {
            overlayVisible = false;
            confirmRequestedBeforeOverlayReady = false;
            windowList = [];
            selectedIndex = 0;
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
}
