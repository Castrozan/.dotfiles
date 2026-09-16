import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

    TestCase {
        name: "WindowSwitcherNavigation"

        function init() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "Win1"
                },
                {
                    address: "b",
                    title: "Win2"
                },
                {
                    address: "c",
                    title: "Win3"
                }
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
}
