pragma Singleton

import ".."
import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: networkUsageServiceRoot

    property int refCount: 0

    readonly property real downloadSpeed: internalDownloadSpeed
    readonly property real uploadSpeed: internalUploadSpeed
    readonly property real downloadTotal: internalDownloadTotal
    readonly property real uploadTotal: internalUploadTotal
    readonly property var downloadHistory: internalDownloadHistory
    readonly property var uploadHistory: internalUploadHistory
    readonly property int historyLength: 30

    property real internalDownloadSpeed: 0
    property real internalUploadSpeed: 0
    property real internalDownloadTotal: 0
    property real internalUploadTotal: 0
    property var internalDownloadHistory: []
    property var internalUploadHistory: []

    property real previousReceivedBytes: 0
    property real previousTransmittedBytes: 0
    property real previousTimestamp: 0

    property real initialReceivedBytes: 0
    property real initialTransmittedBytes: 0
    property bool initialized: false

    function formatBytesPerSecond(bytes: real): var {
        if (bytes < 0 || isNaN(bytes) || !isFinite(bytes))
            return { value: 0, unit: "B/s" };
        if (bytes < 1024)
            return { value: bytes, unit: "B/s" };
        if (bytes < 1024 * 1024)
            return { value: bytes / 1024, unit: "KB/s" };
        if (bytes < 1024 * 1024 * 1024)
            return { value: bytes / (1024 * 1024), unit: "MB/s" };
        return { value: bytes / (1024 * 1024 * 1024), unit: "GB/s" };
    }

    function formatBytesTotal(bytes: real): var {
        if (bytes < 0 || isNaN(bytes) || !isFinite(bytes))
            return { value: 0, unit: "B" };
        if (bytes < 1024)
            return { value: bytes, unit: "B" };
        if (bytes < 1024 * 1024)
            return { value: bytes / 1024, unit: "KB" };
        if (bytes < 1024 * 1024 * 1024)
            return { value: bytes / (1024 * 1024), unit: "MB" };
        return { value: bytes / (1024 * 1024 * 1024), unit: "GB" };
    }

    function parseNetworkDeviceStats(content: string): var {
        const lines = content.split("\n");
        let totalReceived = 0;
        let totalTransmitted = 0;

        for (let i = 2; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line)
                continue;

            const parts = line.split(/\s+/);
            if (parts.length < 10)
                continue;

            const interfaceName = parts[0].replace(":", "");
            if (interfaceName === "lo")
                continue;

            totalReceived += parseFloat(parts[1]) || 0;
            totalTransmitted += parseFloat(parts[9]) || 0;
        }

        return { rx: totalReceived, tx: totalTransmitted };
    }

    FileView {
        id: networkDeviceFileView
        path: "/proc/net/dev"
    }

    Timer {
        interval: DashboardConfig.resourceUpdateInterval
        running: networkUsageServiceRoot.refCount > 0
        repeat: true
        triggeredOnStart: true

        onTriggered: {
            networkDeviceFileView.reload();
            const content = networkDeviceFileView.text();
            if (!content)
                return;

            const data = networkUsageServiceRoot.parseNetworkDeviceStats(content);
            const now = Date.now();

            if (!networkUsageServiceRoot.initialized) {
                networkUsageServiceRoot.initialReceivedBytes = data.rx;
                networkUsageServiceRoot.initialTransmittedBytes = data.tx;
                networkUsageServiceRoot.previousReceivedBytes = data.rx;
                networkUsageServiceRoot.previousTransmittedBytes = data.tx;
                networkUsageServiceRoot.previousTimestamp = now;
                networkUsageServiceRoot.initialized = true;
                return;
            }

            const timeDeltaSeconds = (now - networkUsageServiceRoot.previousTimestamp) / 1000;
            if (timeDeltaSeconds > 0) {
                let receivedDelta = data.rx - networkUsageServiceRoot.previousReceivedBytes;
                let transmittedDelta = data.tx - networkUsageServiceRoot.previousTransmittedBytes;

                if (receivedDelta < 0)
                    receivedDelta += Math.pow(2, 64);
                if (transmittedDelta < 0)
                    transmittedDelta += Math.pow(2, 64);

                networkUsageServiceRoot.internalDownloadSpeed = receivedDelta / timeDeltaSeconds;
                networkUsageServiceRoot.internalUploadSpeed = transmittedDelta / timeDeltaSeconds;

                const maxHistoryLength = networkUsageServiceRoot.historyLength + 1;

                if (networkUsageServiceRoot.internalDownloadSpeed >= 0 && isFinite(networkUsageServiceRoot.internalDownloadSpeed)) {
                    let newDownloadHistory = networkUsageServiceRoot.internalDownloadHistory.slice();
                    newDownloadHistory.push(networkUsageServiceRoot.internalDownloadSpeed);
                    if (newDownloadHistory.length > maxHistoryLength)
                        newDownloadHistory.shift();
                    networkUsageServiceRoot.internalDownloadHistory = newDownloadHistory;
                }

                if (networkUsageServiceRoot.internalUploadSpeed >= 0 && isFinite(networkUsageServiceRoot.internalUploadSpeed)) {
                    let newUploadHistory = networkUsageServiceRoot.internalUploadHistory.slice();
                    newUploadHistory.push(networkUsageServiceRoot.internalUploadSpeed);
                    if (newUploadHistory.length > maxHistoryLength)
                        newUploadHistory.shift();
                    networkUsageServiceRoot.internalUploadHistory = newUploadHistory;
                }
            }

            let downloadTotal = data.rx - networkUsageServiceRoot.initialReceivedBytes;
            let uploadTotal = data.tx - networkUsageServiceRoot.initialTransmittedBytes;
            if (downloadTotal < 0)
                downloadTotal += Math.pow(2, 64);
            if (uploadTotal < 0)
                uploadTotal += Math.pow(2, 64);

            networkUsageServiceRoot.internalDownloadTotal = downloadTotal;
            networkUsageServiceRoot.internalUploadTotal = uploadTotal;

            networkUsageServiceRoot.previousReceivedBytes = data.rx;
            networkUsageServiceRoot.previousTransmittedBytes = data.tx;
            networkUsageServiceRoot.previousTimestamp = now;
        }
    }
}
