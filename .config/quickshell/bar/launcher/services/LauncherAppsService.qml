pragma Singleton
pragma ComponentBehavior: Bound

import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: launcherAppsServiceRoot

    readonly property string usageHistoryDirectoryPath: `${Quickshell.env("HOME")}/.cache/quickshell`
    readonly property string usageHistoryFilePath: `${usageHistoryDirectoryPath}/launcher-usage-history.json`
    property var usageHistoryByAppId: ({})

    function search(queryText: string): list<var> {
        let results = [];
        let lowerQuery = queryText.toLowerCase();
        let allApplications = DesktopEntries.applications.values;

        for (let i = 0; i < allApplications.length; i++) {
            let entry = allApplications[i];
            let nameMatch = entry.name.toLowerCase().includes(lowerQuery);
            let genericNameMatch = entry.genericName && entry.genericName.toLowerCase().includes(lowerQuery);
            let commentMatch = entry.comment && entry.comment.toLowerCase().includes(lowerQuery);
            let keywordsMatch = false;

            if (!nameMatch && !genericNameMatch && !commentMatch) {
                for (let j = 0; j < entry.keywords.length; j++) {
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

        results.sort((entryA, entryB) => {
            let aStartsWith = entryA.name.toLowerCase().startsWith(lowerQuery);
            let bStartsWith = entryB.name.toLowerCase().startsWith(lowerQuery);
            if (aStartsWith && !bStartsWith) return -1;
            if (!aStartsWith && bStartsWith) return 1;

            let aLastUsedTimestamp = usageHistoryByAppId[entryA.id] || 0;
            let bLastUsedTimestamp = usageHistoryByAppId[entryB.id] || 0;
            if (aLastUsedTimestamp !== bLastUsedTimestamp)
                return bLastUsedTimestamp - aLastUsedTimestamp;

            return entryA.name.localeCompare(entryB.name);
        });

        return results;
    }

    function allApplicationsSorted(): list<var> {
        let allApplications = Array.from(DesktopEntries.applications.values);

        allApplications.sort((entryA, entryB) => {
            let aLastUsedTimestamp = usageHistoryByAppId[entryA.id] || 0;
            let bLastUsedTimestamp = usageHistoryByAppId[entryB.id] || 0;
            if (aLastUsedTimestamp !== bLastUsedTimestamp)
                return bLastUsedTimestamp - aLastUsedTimestamp;

            return entryA.name.localeCompare(entryB.name);
        });

        return allApplications;
    }

    function recordAppLaunch(desktopEntry: var): void {
        let updatedHistory = Object.assign({}, usageHistoryByAppId);
        updatedHistory[desktopEntry.id] = Date.now();
        usageHistoryByAppId = updatedHistory;
        _persistUsageHistory();
    }

    function _persistUsageHistory(): void {
        saveUsageHistoryProcess.command = [
            "bash", "-c",
            `mkdir -p '${usageHistoryDirectoryPath}' && cat > '${usageHistoryFilePath}' << 'HISTORY_JSON_EOF'\n${JSON.stringify(usageHistoryByAppId)}\nHISTORY_JSON_EOF`
        ];
        saveUsageHistoryProcess.running = true;
    }

    function _parseLoadedUsageHistory(rawJsonText: string): void {
        try {
            let parsed = JSON.parse(rawJsonText.trim());
            if (parsed && typeof parsed === "object") {
                usageHistoryByAppId = parsed;
            }
        } catch (parseError) {
            usageHistoryByAppId = {};
        }
    }

    Process {
        id: loadUsageHistoryProcess
        command: ["cat", launcherAppsServiceRoot.usageHistoryFilePath]
        running: true

        property string stdoutBuffer: ""

        stdout: SplitParser {
            onRead: data => {
                loadUsageHistoryProcess.stdoutBuffer += data;
            }
        }

        onRunningChanged: {
            if (!running && stdoutBuffer.length > 0) {
                launcherAppsServiceRoot._parseLoadedUsageHistory(stdoutBuffer);
                stdoutBuffer = "";
            }
        }
    }

    Process {
        id: saveUsageHistoryProcess
        running: false
    }
}
