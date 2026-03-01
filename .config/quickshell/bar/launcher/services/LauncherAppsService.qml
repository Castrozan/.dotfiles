pragma Singleton
pragma ComponentBehavior: Bound

import Quickshell
import QtQuick

Singleton {
    id: launcherAppsServiceRoot

    readonly property int maximumResults: 20

    function search(queryText: string): list<var> {
        let results = [];
        let lowerQuery = queryText.toLowerCase();
        let allApplications = DesktopEntries.applications.values;

        for (let i = 0; i < allApplications.length && results.length < maximumResults; i++) {
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
            return entryA.name.localeCompare(entryB.name);
        });

        return results;
    }

    function allApplicationsSorted(): list<var> {
        let allApplications = Array.from(DesktopEntries.applications.values);
        allApplications.sort((entryA, entryB) => entryA.name.localeCompare(entryB.name));
        return allApplications.slice(0, maximumResults);
    }
}
