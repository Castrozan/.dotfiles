import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import QtQuick
import QtQuick.Layouts

Scope {
    id: switcherRoot

    property bool overlayVisible: false
    property bool confirmRequestedBeforeOverlayReady: false
    property int selectedIndex: 0
    property var windowList: []

    SwitcherTheme {
        id: switcherTheme
    }

    function buildFilteredWindowListFromFreshData(freshClientsJson: string): void {
        let freshClients;
        try {
            freshClients = JSON.parse(freshClientsJson);
        } catch (error) {
            return;
        }

        let focusedWorkspaceId = Hyprland.focusedWorkspace ? Hyprland.focusedWorkspace.id : -1;

        let toplevelsMap = {};
        let toplevels = Hyprland.toplevels.values;
        for (let i = 0; i < toplevels.length; i++) {
            let toplevel = toplevels[i];
            toplevelsMap[toplevel.address] = toplevel;
        }

        let filtered = [];
        for (let i = 0; i < freshClients.length; i++) {
            let client = freshClients[i];

            if (!client.workspace || client.workspace.id !== focusedWorkspaceId)
                continue;

            let address = client.address.replace(/^0x/, "");
            let toplevel = toplevelsMap[address];
            if (!toplevel)
                continue;

            filtered.push({
                address: address,
                title: client.title || client.class || "Unknown",
                windowClass: client.class || "",
                waylandHandle: toplevel.wayland,
                focusHistoryId: client.focusHistoryID ?? 9999
            });
        }

        filtered.sort((a, b) => a.focusHistoryId - b.focusHistoryId);
        windowList = filtered;
    }

    function openSwitcher(): void {
        confirmRequestedBeforeOverlayReady = false;
        if (fetchClientsProcess.running)
            fetchClientsProcess.running = false;
        Hyprland.refreshToplevels();
        fetchClientsProcess.running = true;
    }

    function finishOpenSwitcher(): void {
        if (windowList.length === 0)
            return;

        if (confirmRequestedBeforeOverlayReady) {
            let indexToFocus = windowList.length > 1 ? 1 : 0;
            let selectedAddress = windowList[indexToFocus].address;
            Hyprland.dispatch(`focuswindow address:0x${selectedAddress}`);
            closeSwitcher();
            return;
        }

        selectedIndex = windowList.length > 1 ? 1 : 0;
        overlayVisible = true;
    }

    Process {
        id: fetchClientsProcess
        command: ["hyprctl", "clients", "-j"]
        running: false

        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                switcherRoot.buildFilteredWindowListFromFreshData(data);
                switcherRoot.finishOpenSwitcher();
            }
        }
    }

    function clampSelectedIndex(): void {
        if (windowList.length === 0)
            selectedIndex = 0;
        else if (selectedIndex >= windowList.length)
            selectedIndex = windowList.length - 1;
    }

    function selectNextWindow(): void {
        if (!overlayVisible) {
            Hyprland.dispatch("submap reset");
            return;
        }
        if (windowList.length === 0)
            return;
        selectedIndex = (selectedIndex + 1) % windowList.length;
    }

    function selectPreviousWindow(): void {
        if (!overlayVisible) {
            Hyprland.dispatch("submap reset");
            return;
        }
        if (windowList.length === 0)
            return;
        selectedIndex = (selectedIndex - 1 + windowList.length) % windowList.length;
    }

    function confirmSelection(): void {
        if (!overlayVisible) {
            confirmRequestedBeforeOverlayReady = true;
            return;
        }

        clampSelectedIndex();

        if (windowList.length > 0 && selectedIndex < windowList.length) {
            let selectedAddress = windowList[selectedIndex].address;
            Hyprland.dispatch(`focuswindow address:0x${selectedAddress}`);
        }

        closeSwitcher();
    }

    function closeSwitcher(): void {
        overlayVisible = false;
        confirmRequestedBeforeOverlayReady = false;
        windowList = [];
        selectedIndex = 0;
        Hyprland.dispatch("submap reset");
    }

    function cancelSwitcher(): void {
        closeSwitcher();
    }

    SwitcherCommands {
        onOpenRequested: switcherRoot.openSwitcher()
        onNextRequested: switcherRoot.selectNextWindow()
        onPreviousRequested: switcherRoot.selectPreviousWindow()
        onConfirmRequested: switcherRoot.confirmSelection()
        onCancelRequested: switcherRoot.cancelSwitcher()
    }

    SwitcherPanel {
        visible: switcherRoot.overlayVisible
        windowList: switcherRoot.windowList
        selectedIndex: switcherRoot.selectedIndex
        accentColor: switcherTheme.themeAccent
        backgroundColor: switcherTheme.themeBackground
        foregroundColor: switcherTheme.themeForeground
        onCancelRequested: switcherRoot.cancelSwitcher()
        onWindowSelected: index => {
            switcherRoot.selectedIndex = index;
            switcherRoot.confirmSelection();
        }
    }
}
