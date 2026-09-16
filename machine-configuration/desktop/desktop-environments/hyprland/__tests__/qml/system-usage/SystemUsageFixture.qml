import QtQuick

Item {
    id: root

    property QtObject systemUsageLogic: QtObject {
        id: systemUsageLogic

        property real memoryUsedKib: 0
        property real memoryTotalKib: 0
        readonly property real memoryPercentage: memoryTotalKib > 0 ? memoryUsedKib / memoryTotalKib : 0

        property var disks: []
        readonly property real storagePercentage: {
            let totalUsed = 0;
            let totalSize = 0;
            for (const disk of disks) {
                totalUsed += disk.used;
                totalSize += disk.total;
            }
            return totalSize > 0 ? totalUsed / totalSize : 0;
        }

        function cleanCpuName(rawName) {
            return rawName.replace(/\(R\)/gi, "").replace(/\(TM\)/gi, "").replace(/CPU/gi, "").replace(/\d+th Gen /gi, "").replace(/\d+nd Gen /gi, "").replace(/\d+rd Gen /gi, "").replace(/\d+st Gen /gi, "").replace(/Core /gi, "").replace(/Processor/gi, "").replace(/\s+/g, " ").trim();
        }

        function cleanGpuName(rawName) {
            return rawName.replace(/NVIDIA GeForce /gi, "").replace(/NVIDIA /gi, "").replace(/AMD Radeon /gi, "").replace(/AMD /gi, "").replace(/Intel /gi, "").replace(/\(R\)/gi, "").replace(/\(TM\)/gi, "").replace(/Graphics/gi, "").replace(/\s+/g, " ").trim();
        }

        function formatKibibytes(kibibytes) {
            var mib = 1024;
            var gib = 1024 * 1024;
            var tib = 1024 * 1024 * 1024;

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
    }
}
