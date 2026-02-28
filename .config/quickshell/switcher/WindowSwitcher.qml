import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import QtQuick
import QtQuick.Layouts

Scope {
    id: switcherRoot

    property bool overlayVisible: false
    property int selectedIndex: 0
    property var windowList: []

    readonly property string themeColorsPath: `${Quickshell.env("HOME")}/.config/hypr-theme/current/theme/quickshell-osd-colors.json`

    function parseThemeColors(jsonText: string): var {
        try {
            return JSON.parse(jsonText);
        } catch (error) {
            return null;
        }
    }

    function rgbStringToQtColor(rgbString: string, alpha: real): color {
        let parts = rgbString.split(",");
        if (parts.length !== 3) return Qt.rgba(0, 0, 0, alpha);
        return Qt.rgba(
            parseInt(parts[0].trim()) / 255.0,
            parseInt(parts[1].trim()) / 255.0,
            parseInt(parts[2].trim()) / 255.0,
            alpha
        );
    }

    readonly property var themeColors: themeColorsFile.loaded ? parseThemeColors(themeColorsFile.text()) : null

    readonly property color themeBackground: themeColors ? rgbStringToQtColor(themeColors.backgroundRgb, 0.85) : Qt.rgba(0.1, 0.1, 0.1, 0.85)
    readonly property color themeForeground: themeColors ? themeColors.foreground : "white"
    readonly property color themeAccent: themeColors ? themeColors.accent : "#89b4fa"
    readonly property color themeDimOverlay: Qt.rgba(0, 0, 0, 0.25)

    FileView {
        id: themeColorsFile
        path: Qt.url(`file://${themeColorsPath}`)
        watchChanges: true
        blockLoading: true
        onFileChanged: this.reload()
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
        Hyprland.refreshToplevels();
        fetchClientsProcess.running = true;
    }

    function finishOpenSwitcher(): void {
        if (windowList.length === 0)
            return;

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

    function selectNextWindow(): void {
        if (windowList.length === 0) return;
        selectedIndex = (selectedIndex + 1) % windowList.length;
    }

    function selectPreviousWindow(): void {
        if (windowList.length === 0) return;
        selectedIndex = (selectedIndex - 1 + windowList.length) % windowList.length;
    }

    function confirmSelection(): void {
        if (!overlayVisible) return;

        if (windowList.length > 0 && selectedIndex < windowList.length) {
            let selectedAddress = windowList[selectedIndex].address;
            Hyprland.dispatch(`focuswindow address:0x${selectedAddress}`);
        }

        overlayVisible = false;
    }

    function cancelSwitcher(): void {
        overlayVisible = false;
    }

    IpcHandler {
        target: "switcher"

        function open(): void {
            switcherRoot.openSwitcher();
        }

        function next(): void {
            switcherRoot.selectNextWindow();
        }

        function prev(): void {
            switcherRoot.selectPreviousWindow();
        }

        function confirm(): void {
            switcherRoot.confirmSelection();
        }

        function cancel(): void {
            switcherRoot.cancelSwitcher();
        }
    }

    PanelWindow {
        id: switcherPanel

        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }

        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "quickshell-switcher"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

        color: "transparent"
        surfaceFormat.opaque: false

        visible: overlayVisible

        Rectangle {
            anchors.fill: parent
            color: themeDimOverlay
        }

        Item {
            anchors.centerIn: parent

            width: windowListRow.width
            height: windowListRow.height

            Row {
                id: windowListRow
                spacing: 16

                Repeater {
                    model: windowList

                    WindowThumbnailCard {
                        required property var modelData
                        required property int index

                        toplevelHandle: modelData.waylandHandle
                        windowTitle: modelData.title
                        windowClass: modelData.windowClass
                        isSelected: index === selectedIndex
                        accentColor: themeAccent
                        backgroundColor: themeBackground
                        foregroundColor: themeForeground
                    }
                }
            }
        }
    }
}
