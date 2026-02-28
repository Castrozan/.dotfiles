pragma Singleton

import ".."
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

    function cleanCpuName(rawName: string): string {
        return rawName.replace(/\(R\)/gi, "").replace(/\(TM\)/gi, "").replace(/CPU/gi, "").replace(/\d+th Gen /gi, "").replace(/\d+nd Gen /gi, "").replace(/\d+rd Gen /gi, "").replace(/\d+st Gen /gi, "").replace(/Core /gi, "").replace(/Processor/gi, "").replace(/\s+/g, " ").trim();
    }

    function cleanGpuName(rawName: string): string {
        return rawName.replace(/NVIDIA GeForce /gi, "").replace(/NVIDIA /gi, "").replace(/AMD Radeon /gi, "").replace(/AMD /gi, "").replace(/Intel /gi, "").replace(/\(R\)/gi, "").replace(/\(TM\)/gi, "").replace(/Graphics/gi, "").replace(/\s+/g, " ").trim();
    }

    function formatKibibytes(kibibytes: real): var {
        const mib = 1024;
        const gib = 1024 ** 2;
        const tib = 1024 ** 3;

        if (kibibytes >= tib)
            return { value: kibibytes / tib, unit: "TiB" };
        if (kibibytes >= gib)
            return { value: kibibytes / gib, unit: "GiB" };
        if (kibibytes >= mib)
            return { value: kibibytes / mib, unit: "MiB" };
        return { value: kibibytes, unit: "KiB" };
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
            gpuUsageProcess.running = true;
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

    Process {
        id: storageInfoProcess

        command: ["lsblk", "-b", "-o", "NAME,SIZE,TYPE,FSUSED,FSSIZE", "-P"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const diskMap = {};
                const lines = data.trim().split("\n");

                for (const line of lines) {
                    if (line.trim() === "")
                        continue;

                    const nameMatch = line.match(/NAME="([^"]+)"/);
                    const sizeMatch = line.match(/SIZE="([^"]+)"/);
                    const typeMatch = line.match(/TYPE="([^"]+)"/);
                    const fsusedMatch = line.match(/FSUSED="([^"]*)"/);
                    const fssizeMatch = line.match(/FSSIZE="([^"]*)"/);

                    if (!nameMatch || !typeMatch)
                        continue;

                    const name = nameMatch[1];
                    const type = typeMatch[1];
                    const size = parseInt(sizeMatch?.[1] || "0", 10);
                    const fsused = parseInt(fsusedMatch?.[1] || "0", 10);
                    const fssize = parseInt(fssizeMatch?.[1] || "0", 10);

                    if (type === "disk") {
                        if (name.startsWith("zram"))
                            continue;

                        if (!diskMap[name])
                            diskMap[name] = { name: name, totalSize: size, used: 0, fsTotal: 0 };
                    } else if (type === "part") {
                        let parentDisk = name.replace(/p?\d+$/, "");
                        if (name.match(/nvme\d+n\d+p\d+/))
                            parentDisk = name.replace(/p\d+$/, "");

                        if (diskMap[parentDisk]) {
                            diskMap[parentDisk].used += fsused;
                            diskMap[parentDisk].fsTotal += fssize;
                        }
                    }
                }

                const diskList = [];
                for (const diskName of Object.keys(diskMap).sort()) {
                    const disk = diskMap[diskName];
                    const total = disk.fsTotal > 0 ? disk.fsTotal : disk.totalSize;
                    const used = disk.used;
                    const perc = total > 0 ? used / total : 0;

                    diskList.push({
                        mount: disk.name,
                        used: used / 1024,
                        total: total / 1024,
                        free: (total - used) / 1024,
                        perc: perc
                    });
                }

                systemUsageServiceRoot.disks = diskList;
            }
        }
    }

    Process {
        id: gpuNameDetectionProcess

        running: true
        command: ["sh", "-c", "nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || lspci 2>/dev/null | grep -i 'vga\\|3d\\|display' | head -1"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const output = data.trim();
                if (!output)
                    return;

                if (output.toLowerCase().includes("nvidia") || output.toLowerCase().includes("geforce") || output.toLowerCase().includes("rtx") || output.toLowerCase().includes("gtx")) {
                    systemUsageServiceRoot.gpuName = systemUsageServiceRoot.cleanGpuName(output);
                } else {
                    const bracketMatch = output.match(/\[([^\]]+)\]/);
                    if (bracketMatch)
                        systemUsageServiceRoot.gpuName = systemUsageServiceRoot.cleanGpuName(bracketMatch[1]);
                    else {
                        const colonMatch = output.match(/:\s*(.+)/);
                        if (colonMatch)
                            systemUsageServiceRoot.gpuName = systemUsageServiceRoot.cleanGpuName(colonMatch[1]);
                    }
                }
            }
        }
    }

    Process {
        id: gpuTypeDetectionProcess

        running: true
        command: ["sh", "-c", "if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then echo NVIDIA; elif ls /sys/class/drm/card*/device/gpu_busy_percent 2>/dev/null | grep -q .; then echo GENERIC; else echo NONE; fi"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => systemUsageServiceRoot.autoDetectedGpuType = data.trim()
        }
    }

    Process {
        id: gpuUsageProcess

        command: systemUsageServiceRoot.gpuType === "GENERIC"
            ? ["sh", "-c", "cat /sys/class/drm/card*/device/gpu_busy_percent 2>/dev/null || echo 0"]
            : systemUsageServiceRoot.gpuType === "NVIDIA"
                ? ["sh", "-c", "nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,noheader,nounits 2>/dev/null || echo '0, 0'"]
                : ["echo"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                if (systemUsageServiceRoot.gpuType === "GENERIC") {
                    const percentages = data.trim().split("\n");
                    const sum = percentages.reduce((acc, d) => acc + parseInt(d, 10), 0);
                    systemUsageServiceRoot.gpuPercentage = sum / percentages.length / 100;
                } else if (systemUsageServiceRoot.gpuType === "NVIDIA") {
                    const [usage, temp] = data.trim().split(",");
                    systemUsageServiceRoot.gpuPercentage = parseInt(usage, 10) / 100;
                    systemUsageServiceRoot.gpuTemperature = parseInt(temp, 10);
                } else {
                    systemUsageServiceRoot.gpuPercentage = 0;
                    systemUsageServiceRoot.gpuTemperature = 0;
                }
            }
        }
    }

    Process {
        id: sensorTemperatureProcess

        command: ["sensors"]
        environment: ({ LANG: "C.UTF-8", LC_ALL: "C.UTF-8" })
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                let cpuTemp = data.match(/(?:Package id [0-9]+|Tdie):\s+((\+|-)[0-9.]+)(°| )C/);
                if (!cpuTemp)
                    cpuTemp = data.match(/Tctl:\s+((\+|-)[0-9.]+)(°| )C/);

                if (cpuTemp)
                    systemUsageServiceRoot.cpuTemperature = parseFloat(cpuTemp[1]);

                if (systemUsageServiceRoot.gpuType !== "GENERIC")
                    return;

                let eligible = false;
                let sum = 0;
                let count = 0;

                for (const line of data.trim().split("\n")) {
                    if (line === "Adapter: PCI adapter")
                        eligible = true;
                    else if (line === "")
                        eligible = false;
                    else if (eligible) {
                        let match = line.match(/^(temp[0-9]+|GPU core|edge)+:\s+\+([0-9]+\.[0-9]+)(°| )C/);
                        if (!match)
                            match = line.match(/^(junction|mem)+:\s+\+([0-9]+\.[0-9]+)(°| )C/);

                        if (match) {
                            sum += parseFloat(match[2]);
                            count++;
                        }
                    }
                }

                systemUsageServiceRoot.gpuTemperature = count > 0 ? sum / count : 0;
            }
        }
    }
}
