import QtQuick
import QtTest

WindowSwitcherFixture {
    id: root

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
                }
            ];
            windowSwitcher.finishOpenSwitcher();
            compare(windowSwitcher.selectedIndex, 1);
            verify(windowSwitcher.overlayVisible);
        }

        function test_selects_first_window_when_only_one() {
            windowSwitcher.windowList = [
                {
                    address: "a",
                    title: "W1"
                }
            ];
            windowSwitcher.finishOpenSwitcher();
            compare(windowSwitcher.selectedIndex, 0);
            verify(windowSwitcher.overlayVisible);
        }

        function test_handles_confirm_before_overlay_ready() {
            windowSwitcher.confirmRequestedBeforeOverlayReady = true;
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
            windowSwitcher.finishOpenSwitcher();
            verify(!windowSwitcher.overlayVisible);
            verify(!windowSwitcher.confirmRequestedBeforeOverlayReady);
            compare(windowSwitcher.windowList.length, 0);
            compare(windowSwitcher.selectedIndex, 0);
            compare(windowSwitcher.submapResetDispatchCount, 1);
            compare(windowSwitcher.lastFocusedWindowAddress, "b");
        }
    }
}
