import QtQuick
import Quickshell.Hyprland

Connections {
    signal updatesRequested(bool windows, bool monitors, bool layers, bool workspaces, bool activeWorkspace)

    target: Hyprland

    function onRawEvent(event) {
        const eventName = `${event?.name ?? event?.event ?? event?.type ?? ""}`;
        if (["openlayer", "closelayer", "screencast"].includes(eventName))
            return;

        if (eventName === "windowtitle" || eventName === "windowtitlev2") {
            updatesRequested(true, false, false, false, false);
            return;
        }

        if (["openwindow", "closewindow", "movewindow", "movewindowv2", "fullscreen", "changefloatingmode", "pin", "urgent"].includes(eventName)) {
            updatesRequested(true, false, false, true, false);
            return;
        }

        if (["workspace", "workspacev2", "focusedmon", "focusedmonv2", "activewindow", "activewindowv2", "createworkspace", "createworkspacev2", "destroyworkspace", "destroyworkspacev2", "activespecial", "activespecialv2"].includes(eventName)) {
            updatesRequested(false, false, false, true, true);
            return;
        }

        if (eventName.startsWith("monitor") || eventName === "configreloaded") {
            updatesRequested(true, true, false, true, true);
            return;
        }

        updatesRequested(true, true, true, true, true);
    }
}
