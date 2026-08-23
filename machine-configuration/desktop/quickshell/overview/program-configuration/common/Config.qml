pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    property var userOptions: ({})

    property ConfigOptions options: ConfigOptions {
        userOptions: root.userOptions
    }

    Process {
        id: loadUserConfig
        command: [
            "sh",
            "-lc",
            "cfg=\"${XDG_CONFIG_HOME:-$HOME/.config}/quickshell/overview/config.json\"; [ -r \"$cfg\" ] && cat \"$cfg\""
        ]
        stdout: StdioCollector {
            id: configCollector
            onStreamFinished: {
                const payload = configCollector.text.trim();
                if (!payload)
                    return;

                try {
                    const parsed = JSON.parse(payload);
                    if (typeof parsed === "object" && parsed !== null) {
                        root.userOptions = parsed;
                    } else {
                        console.warn("overview: config.json must contain a JSON object; ignoring file");
                    }
                } catch (error) {
                    console.warn("overview: failed to parse user config.json; using defaults", error);
                }
            }
        }
    }

    Component.onCompleted: {
        loadUserConfig.running = true;
    }
}
