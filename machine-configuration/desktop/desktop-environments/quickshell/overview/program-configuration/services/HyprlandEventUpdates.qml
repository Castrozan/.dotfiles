import QtQuick
import Quickshell.Hyprland

Connections {
    signal updatesRequested(bool windows, bool monitors, bool layers, bool workspaces, bool activeWorkspace)

    target: Hyprland

    function onRawEvent(event) {
        const eventName = `${event?.name ?? event?.event ?? event?.type ?? ""}`;
        if (["openlayer", "closelayer", "screencast"].includes(eventName))
            return;

        if (eventName === "openwindow" || eventName === "closewindow" || eventName === "movewindow" || eventName === "movewindowv2" || eventName === "windowtitle") {
            updatesRequested(true, false, false, true, false);
            return;
        }

        if (eventName === "workspace" || eventName === "workspacev2" || eventName === "focusedmon" || eventName === "focusedmonv2" || eventName === "activewindow" || eventName === "activewindowv2") {
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
