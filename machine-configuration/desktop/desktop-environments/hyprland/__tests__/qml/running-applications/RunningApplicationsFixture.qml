import QtQuick

Item {
    id: root

    property QtObject runningAppsModule: QtObject {
        id: runningAppsModule

        property var runningAppsByClass: []
        property string focusedWindowClass: ""
        property var firstSeenOrderByClass: ({})
        property int firstSeenOrderNextIndex: 0

        readonly property var windowClassToIconName: ({
                "chrome-global": "google-chrome",
                "code": "vscode",
                "code - insiders": "vscode-insiders",
                "cursor": "cursor"
            })

        function resolveIconName(windowClass) {
            var lowerClass = windowClass.toLowerCase();
            var mapped = windowClassToIconName[lowerClass];
            return mapped !== undefined ? mapped : lowerClass;
        }

        function parseClientsAndRebuildAppList(clientsJson) {
            var clients;
            try {
                clients = JSON.parse(clientsJson);
            } catch (error) {
                return;
            }

            var mostRecentWindowByClass = {};
            var detectedFocusedClass = "";

            for (var i = 0; i < clients.length; i++) {
                var client = clients[i];
                var windowClass = client["class"] || "";
                if (windowClass === "")
                    continue;

                if (client.focusHistoryID === 0)
                    detectedFocusedClass = windowClass;

                var existing = mostRecentWindowByClass[windowClass];
                var clientFocusId = client.focusHistoryID !== undefined ? client.focusHistoryID : 9999;
                if (!existing || (clientFocusId < existing.focusHistoryID)) {
                    mostRecentWindowByClass[windowClass] = {
                        windowClass: windowClass,
                        address: client.address,
                        focusHistoryID: clientFocusId
                    };
                }
            }

            var updatedFirstSeenOrder = {};
            for (var key in firstSeenOrderByClass) {
                updatedFirstSeenOrder[key] = firstSeenOrderByClass[key];
            }
            var updatedNextIndex = firstSeenOrderNextIndex;

            for (var cls in mostRecentWindowByClass) {
                if (updatedFirstSeenOrder[cls] === undefined) {
                    updatedFirstSeenOrder[cls] = updatedNextIndex;
                    updatedNextIndex++;
                }
            }

            for (var cls2 in updatedFirstSeenOrder) {
                if (!mostRecentWindowByClass[cls2])
                    delete updatedFirstSeenOrder[cls2];
            }

            firstSeenOrderByClass = updatedFirstSeenOrder;
            firstSeenOrderNextIndex = updatedNextIndex;

            var sortedAppList = [];
            for (var cls3 in mostRecentWindowByClass)
                sortedAppList.push(mostRecentWindowByClass[cls3]);

            sortedAppList.sort(function (a, b) {
                return firstSeenOrderByClass[a.windowClass] - firstSeenOrderByClass[b.windowClass];
            });

            runningAppsByClass = sortedAppList;
            focusedWindowClass = detectedFocusedClass;
        }
    }
}
