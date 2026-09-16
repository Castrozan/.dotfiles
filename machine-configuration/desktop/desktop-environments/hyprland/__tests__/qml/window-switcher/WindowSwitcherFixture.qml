import QtQuick

Item {
    id: root

    property QtObject windowSwitcher: QtObject {
        id: windowSwitcher

        property bool overlayVisible: false
        property bool confirmRequestedBeforeOverlayReady: false
        property int selectedIndex: 0
        property var windowList: []
        property int submapResetDispatchCount: 0
        property string lastFocusedWindowAddress: ""

        function buildFilteredWindowListFromFreshData(freshClientsJson, focusedWorkspaceId, toplevelsMap) {
            var freshClients;
            try {
                freshClients = JSON.parse(freshClientsJson);
            } catch (error) {
                return;
            }

            var filtered = [];
            for (var i = 0; i < freshClients.length; i++) {
                var client = freshClients[i];

                if (!client.workspace || client.workspace.id !== focusedWorkspaceId)
                    continue;

                var address = client.address.replace(/^0x/, "");
                var toplevel = toplevelsMap[address];
                if (!toplevel)
                    continue;

                filtered.push({
                    address: address,
                    title: client.title || client.class || "Unknown",
                    windowClass: client.class || "",
                    focusHistoryId: client.focusHistoryID !== undefined ? client.focusHistoryID : 9999
                });
            }

            filtered.sort(function (a, b) {
                return a.focusHistoryId - b.focusHistoryId;
            });
            windowList = filtered;
        }

        function clampSelectedIndex() {
            if (windowList.length === 0)
                selectedIndex = 0;
            else if (selectedIndex >= windowList.length)
                selectedIndex = windowList.length - 1;
        }

        function selectNextWindow() {
            if (windowList.length === 0)
                return;
            selectedIndex = (selectedIndex + 1) % windowList.length;
        }

        function selectPreviousWindow() {
            if (windowList.length === 0)
                return;
            selectedIndex = (selectedIndex - 1 + windowList.length) % windowList.length;
        }

        function finishOpenSwitcher() {
            if (windowList.length === 0)
                return;

            if (confirmRequestedBeforeOverlayReady) {
                var indexToFocus = windowList.length > 1 ? 1 : 0;
                lastFocusedWindowAddress = windowList[indexToFocus].address;
                closeSwitcher();
                return;
            }

            selectedIndex = windowList.length > 1 ? 1 : 0;
            overlayVisible = true;
        }

        function confirmSelection() {
            if (!overlayVisible) {
                confirmRequestedBeforeOverlayReady = true;
                return;
            }

            clampSelectedIndex();
            if (windowList.length > 0 && selectedIndex < windowList.length)
                lastFocusedWindowAddress = windowList[selectedIndex].address;
            closeSwitcher();
        }

        function closeSwitcher() {
            overlayVisible = false;
            confirmRequestedBeforeOverlayReady = false;
            windowList = [];
            selectedIndex = 0;
            submapResetDispatchCount++;
        }

        function cancelSwitcher() {
            closeSwitcher();
        }

        function parseThemeColors(jsonText) {
            try {
                return JSON.parse(jsonText);
            } catch (error) {
                return null;
            }
        }

        function rgbStringToQtColor(rgbString, alpha) {
            var parts = rgbString.split(",");
            if (parts.length !== 3)
                return Qt.rgba(0, 0, 0, alpha);
            return Qt.rgba(parseInt(parts[0].trim()) / 255.0, parseInt(parts[1].trim()) / 255.0, parseInt(parts[2].trim()) / 255.0, alpha);
        }
    }

    property var sampleToplevelsMap: ({
            "abc123": {
                wayland: "wl-abc123"
            },
            "def456": {
                wayland: "wl-def456"
            },
            "ghi789": {
                wayland: "wl-ghi789"
            }
        })

    property string sampleClientsJson: JSON.stringify([
        {
            address: "0xabc123",
            title: "Firefox",
            "class": "firefox",
            workspace: {
                id: 1
            },
            focusHistoryID: 2
        },
        {
            address: "0xdef456",
            title: "Terminal",
            "class": "kitty",
            workspace: {
                id: 1
            },
            focusHistoryID: 0
        },
        {
            address: "0xghi789",
            title: "Code",
            "class": "code",
            workspace: {
                id: 2
            },
            focusHistoryID: 1
        }
    ])
}
