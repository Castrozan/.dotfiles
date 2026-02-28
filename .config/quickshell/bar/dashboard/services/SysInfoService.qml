pragma Singleton

import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: sysInfoServiceRoot

    property string osName
    property string osPrettyName
    property string osId
    property string uptime

    readonly property string user: Quickshell.env("USER")
    readonly property string windowManager: Quickshell.env("XDG_CURRENT_DESKTOP") || Quickshell.env("XDG_SESSION_DESKTOP")
    readonly property string shell: Quickshell.env("SHELL").split("/").pop()
    readonly property string faceIconPath: user ? `file:///home/${user}/.face` : ""

    FileView {
        id: osReleaseFileView

        path: "/etc/os-release"
        onLoaded: {
            const lines = text().split("\n");
            const findValue = key => lines.find(l => l.startsWith(`${key}=`))?.split("=")[1].replace(/"/g, "") ?? "";

            sysInfoServiceRoot.osName = findValue("NAME");
            sysInfoServiceRoot.osPrettyName = findValue("PRETTY_NAME");
            sysInfoServiceRoot.osId = findValue("ID");
        }
    }

    Timer {
        running: true
        repeat: true
        interval: 15000
        onTriggered: uptimeFileView.reload()
    }

    FileView {
        id: uptimeFileView

        path: "/proc/uptime"
        onLoaded: {
            const uptimeSeconds = parseInt(text().split(" ")[0] ?? 0);

            const days = Math.floor(uptimeSeconds / 86400);
            const hours = Math.floor((uptimeSeconds % 86400) / 3600);
            const minutes = Math.floor((uptimeSeconds % 3600) / 60);

            let formattedUptime = "";
            if (days > 0)
                formattedUptime += `${days} day${days === 1 ? "" : "s"}`;
            if (hours > 0)
                formattedUptime += `${formattedUptime ? ", " : ""}${hours} hour${hours === 1 ? "" : "s"}`;
            if (minutes > 0 || !formattedUptime)
                formattedUptime += `${formattedUptime ? ", " : ""}${minutes} minute${minutes === 1 ? "" : "s"}`;
            sysInfoServiceRoot.uptime = formattedUptime;
        }
    }
}
