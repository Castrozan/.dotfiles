pragma Singleton

import ".."
import "system-usage"
import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: systemUsageServiceRoot

    property string cpuName: ""
    property real cpuPercentage
    property real cpuTemperature

    readonly property string gpuType: autoDetectedGpuType
    property string autoDetectedGpuType: "NONE"
    property string gpuName: ""
    property real gpuPercentage
    property real gpuTemperature

    property real memoryUsedKib
    property real memoryTotalKib
    readonly property real memoryPercentage: memoryTotalKib > 0 ? memoryUsedKib / memoryTotalKib : 0

    readonly property real storagePercentage: {
        let totalUsed = 0;
        let totalSize = 0;
        for (const disk of disks) {
            totalUsed += disk.used;
            totalSize += disk.total;
        }
        return totalSize > 0 ? totalUsed / totalSize : 0;
    }

    property var disks: []

    property real previousCpuIdle
    property real previousCpuTotal

    property int refCount
    property bool gpuDetectionStarted: false

    onRefCountChanged: {
        if (refCount > 0 && !gpuDetectionStarted) {
            gpuDetectionStarted = true;
            graphicsUsage.detect();
        }
    }

    function cleanCpuName(rawName: string): string {
        return rawName.replace(/\(R\)/gi, "").replace(/\(TM\)/gi, "").replace(/CPU/gi, "").replace(/\d+th Gen /gi, "").replace(/\d+nd Gen /gi, "").replace(/\d+rd Gen /gi, "").replace(/\d+st Gen /gi, "").replace(/Core /gi, "").replace(/Processor/gi, "").replace(/\s+/g, " ").trim();
    }

    function formatKibibytes(kibibytes: real): var {
        const mib = 1024;
        const gib = 1024 ** 2;
        const tib = 1024 ** 3;

        if (kibibytes >= tib)
            return {
                value: kibibytes / tib,
                unit: "TiB"
            };
        if (kibibytes >= gib)
            return {
                value: kibibytes / gib,
                unit: "GiB"
            };
        if (kibibytes >= mib)
            return {
                value: kibibytes / mib,
                unit: "MiB"
            };
        return {
            value: kibibytes,
            unit: "KiB"
        };
    }

    Timer {
        running: systemUsageServiceRoot.refCount > 0
        interval: DashboardConfig.resourceUpdateInterval
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            cpuStatFileView.reload();
            memoryInfoFileView.reload();
            storageInfoProcess.running = true;
            graphicsUsage.refresh();
            sensorTemperatureProcess.running = true;
        }
    }

    FileView {
        id: cpuInfoInitFileView

        path: "/proc/cpuinfo"
        onLoaded: {
            const nameMatch = text().match(/model name\s*:\s*(.+)/);
            if (nameMatch)
                systemUsageServiceRoot.cpuName = systemUsageServiceRoot.cleanCpuName(nameMatch[1]);
        }
    }

    FileView {
        id: cpuStatFileView

        path: "/proc/stat"
        onLoaded: {
            const data = text().match(/^cpu\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)/);
            if (data) {
                const stats = data.slice(1).map(n => parseInt(n, 10));
                const total = stats.reduce((a, b) => a + b, 0);
                const idle = stats[3] + (stats[4] ?? 0);

                const totalDifference = total - systemUsageServiceRoot.previousCpuTotal;
                const idleDifference = idle - systemUsageServiceRoot.previousCpuIdle;
                systemUsageServiceRoot.cpuPercentage = totalDifference > 0 ? (1 - idleDifference / totalDifference) : 0;

                systemUsageServiceRoot.previousCpuTotal = total;
                systemUsageServiceRoot.previousCpuIdle = idle;
            }
        }
    }

    FileView {
        id: memoryInfoFileView

        path: "/proc/meminfo"
        onLoaded: {
            const data = text();
            systemUsageServiceRoot.memoryTotalKib = parseInt(data.match(/MemTotal: *(\d+)/)[1], 10) || 1;
            systemUsageServiceRoot.memoryUsedKib = (systemUsageServiceRoot.memoryTotalKib - parseInt(data.match(/MemAvailable: *(\d+)/)[1], 10)) || 0;
        }
    }

    StorageUsage {
        id: storageInfoProcess
        onDisksRead: disks => systemUsageServiceRoot.disks = disks
    }

    GraphicsUsage {
        id: graphicsUsage
        gpuType: systemUsageServiceRoot.gpuType
        onNameDiscovered: name => systemUsageServiceRoot.gpuName = name
        onTypeDiscovered: type => systemUsageServiceRoot.autoDetectedGpuType = type
        onUsageDiscovered: percentage => systemUsageServiceRoot.gpuPercentage = percentage
        onTemperatureDiscovered: temperature => systemUsageServiceRoot.gpuTemperature = temperature
    }

    HardwareTemperatures {
        id: sensorTemperatureProcess
        gpuType: systemUsageServiceRoot.gpuType
        onCpuTemperatureRead: temperature => systemUsageServiceRoot.cpuTemperature = temperature
        onGpuTemperatureRead: temperature => systemUsageServiceRoot.gpuTemperature = temperature
    }
}
