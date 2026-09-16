import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

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

        function test_nav_on_single_window_stays_at_zero() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                }
            ];
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 0);
            windowSwitcher.selectPreviousWindow();
            compare(windowSwitcher.selectedIndex, 0);
        }

        function test_nav_on_two_windows_toggles() {
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
            windowSwitcher.selectedIndex = 0;
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 1);
            windowSwitcher.selectNextWindow();
            compare(windowSwitcher.selectedIndex, 0);
            windowSwitcher.selectPreviousWindow();
            compare(windowSwitcher.selectedIndex, 1);
        }

        function test_rapid_next_next_next_confirm_cycle() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                },
                {
                    address: "b",
                    title: "W2"
                },
                {
                    address: "c",
                    title: "W3"
                },
                {
                    address: "d",
                    title: "W4"
                },
                {
                    address: "e",
                    title: "W5"
                }
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
                {
                    address: "a",
                    title: "W1"
                },
                {
                    address: "b",
                    title: "W2"
                },
                {
                    address: "c",
                    title: "W3"
                },
                {
                    address: "d",
                    title: "W4"
                },
                {
                    address: "e",
                    title: "W5"
                }
            ];
            windowSwitcher.selectedIndex = 4;
            windowSwitcher.overlayVisible = true;

            // Windows shrink (e.g., 3 closed between overlay open and confirm)
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
            // Confirm should clamp
            windowSwitcher.confirmSelection();
            // selectedIndex was 4, clamped to 1 (length-1), then reset to 0 after confirm
            compare(windowSwitcher.selectedIndex, 0);
        }
    }
}
