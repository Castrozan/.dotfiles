pragma Singleton

import ".."
import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: cavaServiceRoot

    readonly property int barCount: 24
    property var values: Array(barCount).fill(0)

    property int refCount: 0

    Process {
        id: cavaProcess

        running: cavaServiceRoot.refCount > 0
        command: ["cava", "-p", Qt.resolvedUrl("../../assets/cava-bar.conf").toString().replace("file://", "")]

        stdout: SplitParser {
            onRead: data => {
                const rawValues = data.trim().split(";").filter(s => s !== "");
                if (rawValues.length === 0)
                    return;

                const normalizedValues = rawValues.map(v => Math.min(1.0, parseInt(v, 10) / 100));
                cavaServiceRoot.values = normalizedValues;
            }
        }

        onRunningChanged: {
            if (!running)
                cavaServiceRoot.values = Array(cavaServiceRoot.barCount).fill(0);
        }
    }
}
