import QtQuick
import QtTest
import Quickshell.Hyprland
import "../../../../../quickshell/overview/program-configuration/services"
import "../../../../../quickshell/overview/program-configuration/common"

Item {
    TestCase {
        name: "HyprlandDataLifecycle"

        function queries() {
            return HyprlandData.children.find(child => child.refresh !== undefined).children;
        }

        function finishAll() {
            for (const query of queries()) {
                if (!query.running)
                    continue;
                query.running = false;
                query.exited(0, 0);
            }
        }

        function init() {
            GlobalStates.overviewOpen = false;
            Config.userOptions = {
                hacks: {
                    hyprlandEventDebounceMs: 20
                }
            };
            finishAll();
        }

        function cleanup() {
            GlobalStates.overviewOpen = false;
            finishAll();
        }

        function test_closed_overview_ignores_event_churn() {
            for (let index = 0; index < 100; index++) {
                Hyprland.rawEvent({
                    name: "windowtitlev2"
                });
                Hyprland.rawEvent({
                    name: "activewindowv2"
                });
            }
            wait(30);
            compare(queries().length, 5);
            for (const query of queries())
                verify(!query.running);
        }

        function test_opening_refreshes_without_waiting_for_debounce() {
            GlobalStates.overviewOpen = true;
            wait(0);
            for (const query of queries())
                verify(query.running);
        }

        function test_closing_cancels_debounced_refresh() {
            GlobalStates.overviewOpen = true;
            wait(0);
            finishAll();
            Hyprland.rawEvent({
                name: "windowtitlev2"
            });
            verify(HyprlandData.pendingWindowsUpdate);
            GlobalStates.overviewOpen = false;
            wait(30);
            verify(!HyprlandData.pendingWindowsUpdate);
            for (const query of queries())
                verify(!query.running);
        }

        function test_reopening_during_queries_preserves_fresh_refresh() {
            GlobalStates.overviewOpen = true;
            wait(0);
            GlobalStates.overviewOpen = false;
            GlobalStates.overviewOpen = true;
            wait(0);
            finishAll();
            for (const query of queries())
                verify(query.running);
            finishAll();
            for (const query of queries())
                verify(!query.running);
        }
    }
}
