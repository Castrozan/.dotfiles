import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

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
                windows.push({
                    address: "addr" + i,
                    title: "Window " + i
                });
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
                toplevels[addr] = {
                    wayland: "wl-" + addr
                };
                clients.push({
                    address: "0x" + addr,
                    title: "App " + i,
                    "class": "app" + i,
                    workspace: {
                        id: 1
                    },
                    focusHistoryID: 29 - i // Reverse order
                });
            }
            windowSwitcher.buildFilteredWindowListFromFreshData(JSON.stringify(clients), 1, toplevels);
            compare(windowSwitcher.windowList.length, 30);
            // Should be sorted: focusHistoryId 0 first (which is app29)
            compare(windowSwitcher.windowList[0].title, "App 29");
            compare(windowSwitcher.windowList[0].focusHistoryId, 0);
            compare(windowSwitcher.windowList[29].title, "App 0");
            compare(windowSwitcher.windowList[29].focusHistoryId, 29);
        }
    }
}
