import QtQuick

Item {
    id: root

    property QtObject launcherAppsService: QtObject {
        id: launcherAppsService

        property var usageHistoryByAppId: ({})

        function search(queryText, allApplications) {
            var results = [];
            var lowerQuery = queryText.toLowerCase();

            for (var i = 0; i < allApplications.length; i++) {
                var entry = allApplications[i];
                var nameMatch = entry.name.toLowerCase().includes(lowerQuery);
                var genericNameMatch = entry.genericName && entry.genericName.toLowerCase().includes(lowerQuery);
                var commentMatch = entry.comment && entry.comment.toLowerCase().includes(lowerQuery);
                var keywordsMatch = false;

                if (!nameMatch && !genericNameMatch && !commentMatch) {
                    for (var j = 0; j < entry.keywords.length; j++) {
                        if (entry.keywords[j].toLowerCase().includes(lowerQuery)) {
                            keywordsMatch = true;
                            break;
                        }
                    }
                }

                if (nameMatch || genericNameMatch || commentMatch || keywordsMatch) {
                    results.push(entry);
                }
            }

            results.sort(function (entryA, entryB) {
                var aStartsWith = entryA.name.toLowerCase().startsWith(lowerQuery);
                var bStartsWith = entryB.name.toLowerCase().startsWith(lowerQuery);
                if (aStartsWith && !bStartsWith)
                    return -1;
                if (!aStartsWith && bStartsWith)
                    return 1;

                var aLastUsedTimestamp = usageHistoryByAppId[entryA.id] || 0;
                var bLastUsedTimestamp = usageHistoryByAppId[entryB.id] || 0;
                if (aLastUsedTimestamp !== bLastUsedTimestamp)
                    return bLastUsedTimestamp - aLastUsedTimestamp;

                return entryA.name.localeCompare(entryB.name);
            });

            return results;
        }

        function allApplicationsSorted(allApplications) {
            var sorted = allApplications.slice();
            sorted.sort(function (entryA, entryB) {
                var aLastUsedTimestamp = usageHistoryByAppId[entryA.id] || 0;
                var bLastUsedTimestamp = usageHistoryByAppId[entryB.id] || 0;
                if (aLastUsedTimestamp !== bLastUsedTimestamp)
                    return bLastUsedTimestamp - aLastUsedTimestamp;
                return entryA.name.localeCompare(entryB.name);
            });
            return sorted;
        }

        function parseLoadedUsageHistory(rawJsonText) {
            try {
                var parsed = JSON.parse(rawJsonText.trim());
                if (parsed && typeof parsed === "object") {
                    usageHistoryByAppId = parsed;
                    return true;
                }
            } catch (parseError) {
                usageHistoryByAppId = {};
            }
            return false;
        }
    }

    property var sampleApplications: [
        {
            id: "firefox",
            name: "Firefox",
            genericName: "Web Browser",
            comment: "Browse the web",
            keywords: ["internet", "www"]
        },
        {
            id: "chromium",
            name: "Chromium",
            genericName: "Web Browser",
            comment: "",
            keywords: ["internet", "chrome"]
        },
        {
            id: "kitty",
            name: "Kitty",
            genericName: "Terminal Emulator",
            comment: "GPU accelerated terminal",
            keywords: ["shell", "console"]
        },
        {
            id: "nautilus",
            name: "Files",
            genericName: "File Manager",
            comment: "Access and organize files",
            keywords: ["folder", "directory"]
        },
        {
            id: "code",
            name: "Visual Studio Code",
            genericName: "Text Editor",
            comment: "Code editing",
            keywords: ["vscode", "editor"]
        }
    ]
}
