import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

    TestCase {
        name: "WindowSwitcherConfirmAndCancel"

        function init() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                },
                {
                    address: "b",
                    title: "W2"
                }
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
}
