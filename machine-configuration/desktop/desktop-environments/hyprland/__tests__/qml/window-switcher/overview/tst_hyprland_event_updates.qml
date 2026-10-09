import QtQuick
import QtTest
import Quickshell.Hyprland
import "../../../../../quickshell/overview/program-configuration/services"

Item {
    HyprlandEventUpdates {
        id: updates
    }

    SignalSpy {
        id: requests
        target: updates
        signalName: "updatesRequested"
    }

    TestCase {
        name: "HyprlandEventUpdates"

        function init() {
            updates.enabled = true;
            requests.clear();
        }

        function test_disabled_subscription_ignores_events() {
            updates.enabled = false;
            Hyprland.rawEvent({
                name: "activewindowv2"
            });
            Hyprland.rawEvent({
                name: "windowtitlev2"
            });
            Hyprland.rawEvent({
                name: "unknown"
            });
            compare(requests.count, 0);
        }

        function test_titles_refresh_only_windows() {
            for (const name of ["windowtitle", "windowtitlev2"])
                Hyprland.rawEvent({
                    name
                });
            compare(requests.count, 2);
            for (const request of requests.signalArguments)
                compare(Array.from(request), [true, false, false, false, false]);
        }

        function test_focus_and_workspace_changes_preserve_scope() {
            for (const name of ["activewindowv2", "workspacev2", "focusedmonv2", "createworkspacev2", "destroyworkspacev2", "activespecialv2"])
                Hyprland.rawEvent({
                    name
                });
            compare(requests.count, 6);
            for (const request of requests.signalArguments)
                compare(Array.from(request), [false, false, false, true, true]);
        }

        function test_window_state_changes_refresh_clients_and_workspaces() {
            for (const name of ["openwindow", "closewindow", "movewindowv2", "fullscreen", "changefloatingmode", "pin", "urgent"])
                Hyprland.rawEvent({
                    name
                });
            compare(requests.count, 7);
            for (const request of requests.signalArguments)
                compare(Array.from(request), [true, false, false, true, false]);
        }

        function test_layer_capture_events_do_not_refresh() {
            for (const name of ["openlayer", "closelayer", "screencast"])
                Hyprland.rawEvent({
                    name
                });
            compare(requests.count, 0);
        }

        function test_unknown_events_refresh_all_data_when_enabled() {
            Hyprland.rawEvent({
                name: "future-event"
            });
            compare(requests.count, 1);
            compare(Array.from(requests.signalArguments[0]), [true, true, true, true, true]);
        }

        function test_reenabled_subscription_receives_updates() {
            updates.enabled = false;
            Hyprland.rawEvent({
                name: "windowtitlev2"
            });
            updates.enabled = true;
            Hyprland.rawEvent({
                name: "windowtitlev2"
            });
            compare(requests.count, 1);
        }
    }
}
