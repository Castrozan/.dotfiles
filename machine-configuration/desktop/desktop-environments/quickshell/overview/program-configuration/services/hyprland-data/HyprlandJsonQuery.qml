import Quickshell.Io

Process {
    id: query

    required property string queryName
    property bool active: true
    property bool refreshPending: false

    signal responseReceived(var response)

    command: ["hyprctl", queryName, "-j"]

    function refresh(): void {
        if (!active)
            return;
        if (running) {
            refreshPending = true;
            return;
        }
        running = true;
    }

    onActiveChanged: {
        if (!active)
            refreshPending = false;
    }

    onExited: {
        if (!active || !refreshPending)
            return;
        refreshPending = false;
        running = true;
    }

    stdout: StdioCollector {
        onStreamFinished: query.responseReceived(JSON.parse(text))
    }
}
