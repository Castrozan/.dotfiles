import QtQuick
import QtTest

Item {
    id: root

    QtObject {
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
                return { value: kibibytes / tib, unit: "TiB" };
            if (kibibytes >= gib)
                return { value: kibibytes / gib, unit: "GiB" };
            if (kibibytes >= mib)
                return { value: kibibytes / mib, unit: "MiB" };
            return { value: kibibytes, unit: "KiB" };
        }
    }

    TestCase {
        name: "SystemUsageServiceCleanCpuName"

        function test_removes_registered_trademark() {
            compare(systemUsageLogic.cleanCpuName("Intel(R) Xeon(R)"), "Intel Xeon");
        }

        function test_removes_trademark() {
            compare(systemUsageLogic.cleanCpuName("Intel(TM) i7"), "Intel i7");
        }

        function test_removes_cpu_keyword() {
            compare(systemUsageLogic.cleanCpuName("Intel Core i7-14700K CPU @ 3.40GHz"), "Intel i7-14700K @ 3.40GHz");
        }

        function test_removes_generation_prefix() {
            compare(systemUsageLogic.cleanCpuName("14th Gen Intel Core i7-14700K"), "Intel i7-14700K");
        }

        function test_removes_2nd_gen() {
            compare(systemUsageLogic.cleanCpuName("2nd Gen Intel Core i5-2500"), "Intel i5-2500");
        }

        function test_removes_3rd_gen() {
            compare(systemUsageLogic.cleanCpuName("3rd Gen Intel Core i7-3770"), "Intel i7-3770");
        }

        function test_removes_1st_gen() {
            compare(systemUsageLogic.cleanCpuName("1st Gen AMD Ryzen"), "AMD Ryzen");
        }

        function test_removes_processor_keyword() {
            compare(systemUsageLogic.cleanCpuName("AMD Ryzen 9 5950X Processor"), "AMD Ryzen 9 5950X");
        }

        function test_removes_core_keyword() {
            compare(systemUsageLogic.cleanCpuName("Intel Core i9-13900K"), "Intel i9-13900K");
        }

        function test_collapses_multiple_spaces() {
            compare(systemUsageLogic.cleanCpuName("Intel    i7   14700K"), "Intel i7 14700K");
        }

        function test_trims_whitespace() {
            compare(systemUsageLogic.cleanCpuName("  Intel i7  "), "Intel i7");
        }

        function test_full_realistic_cpu_name() {
            compare(systemUsageLogic.cleanCpuName("14th Gen Intel(R) Core(TM) i7-14700K CPU @ 3.40GHz"), "Intel i7-14700K @ 3.40GHz");
        }

        function test_amd_cpu_name() {
            compare(systemUsageLogic.cleanCpuName("AMD Ryzen 9 7950X 16-Core Processor"), "AMD Ryzen 9 7950X 16-");
        }

        function test_empty_string() {
            compare(systemUsageLogic.cleanCpuName(""), "");
        }
    }

    TestCase {
        name: "SystemUsageServiceCleanGpuName"

        function test_removes_nvidia_geforce_prefix() {
            compare(systemUsageLogic.cleanGpuName("NVIDIA GeForce RTX 4090"), "RTX 4090");
        }

        function test_removes_nvidia_prefix() {
            compare(systemUsageLogic.cleanGpuName("NVIDIA RTX A6000"), "RTX A6000");
        }

        function test_removes_amd_radeon_prefix() {
            compare(systemUsageLogic.cleanGpuName("AMD Radeon RX 7900 XTX"), "RX 7900 XTX");
        }

        function test_removes_amd_prefix() {
            compare(systemUsageLogic.cleanGpuName("AMD RX 580"), "RX 580");
        }

        function test_removes_intel_prefix() {
            compare(systemUsageLogic.cleanGpuName("Intel UHD 770"), "UHD 770");
        }

        function test_removes_registered_and_trademark_after_intel() {
            compare(systemUsageLogic.cleanGpuName("Intel(R) UHD(TM) 770"), "Intel UHD 770");
        }

        function test_intel_with_space_before_registered() {
            compare(systemUsageLogic.cleanGpuName("Intel (R) UHD Graphics 770"), "UHD 770");
        }

        function test_removes_graphics_keyword() {
            compare(systemUsageLogic.cleanGpuName("Intel HD Graphics 630"), "HD 630");
        }

        function test_collapses_multiple_spaces() {
            compare(systemUsageLogic.cleanGpuName("NVIDIA   GeForce   RTX   4090"), "GeForce RTX 4090");
        }

        function test_empty_string() {
            compare(systemUsageLogic.cleanGpuName(""), "");
        }

        function test_unknown_gpu_passthrough() {
            compare(systemUsageLogic.cleanGpuName("Matrox G200eR2"), "Matrox G200eR2");
        }
    }

    TestCase {
        name: "SystemUsageServiceFormatKibibytes"

        function test_small_value_returns_kib() {
            var result = systemUsageLogic.formatKibibytes(512);
            compare(result.unit, "KiB");
            compare(result.value, 512);
        }

        function test_zero_returns_kib() {
            var result = systemUsageLogic.formatKibibytes(0);
            compare(result.unit, "KiB");
            compare(result.value, 0);
        }

        function test_exactly_one_mib() {
            var result = systemUsageLogic.formatKibibytes(1024);
            compare(result.unit, "MiB");
            fuzzyCompare(result.value, 1.0, 0.001);
        }

        function test_several_mib() {
            var result = systemUsageLogic.formatKibibytes(2048);
            compare(result.unit, "MiB");
            fuzzyCompare(result.value, 2.0, 0.001);
        }

        function test_exactly_one_gib() {
            var result = systemUsageLogic.formatKibibytes(1024 * 1024);
            compare(result.unit, "GiB");
            fuzzyCompare(result.value, 1.0, 0.001);
        }

        function test_sixteen_gib() {
            var result = systemUsageLogic.formatKibibytes(16 * 1024 * 1024);
            compare(result.unit, "GiB");
            fuzzyCompare(result.value, 16.0, 0.001);
        }

        function test_exactly_one_tib() {
            var result = systemUsageLogic.formatKibibytes(1024 * 1024 * 1024);
            compare(result.unit, "TiB");
            fuzzyCompare(result.value, 1.0, 0.001);
        }

        function test_just_under_one_mib() {
            var result = systemUsageLogic.formatKibibytes(1023);
            compare(result.unit, "KiB");
            compare(result.value, 1023);
        }

        function test_just_under_one_gib() {
            var result = systemUsageLogic.formatKibibytes(1024 * 1024 - 1);
            compare(result.unit, "MiB");
        }
    }

    TestCase {
        name: "SystemUsageServiceMemoryPercentage"

        function test_normal_memory_usage() {
            systemUsageLogic.memoryTotalKib = 16 * 1024 * 1024;
            systemUsageLogic.memoryUsedKib = 8 * 1024 * 1024;
            fuzzyCompare(systemUsageLogic.memoryPercentage, 0.5, 0.001);
        }

        function test_zero_total_returns_zero() {
            systemUsageLogic.memoryTotalKib = 0;
            systemUsageLogic.memoryUsedKib = 1000;
            compare(systemUsageLogic.memoryPercentage, 0);
        }

        function test_full_memory() {
            systemUsageLogic.memoryTotalKib = 1000;
            systemUsageLogic.memoryUsedKib = 1000;
            fuzzyCompare(systemUsageLogic.memoryPercentage, 1.0, 0.001);
        }

        function test_no_memory_used() {
            systemUsageLogic.memoryTotalKib = 1000;
            systemUsageLogic.memoryUsedKib = 0;
            compare(systemUsageLogic.memoryPercentage, 0);
        }
    }

    TestCase {
        name: "SystemUsageServiceStoragePercentage"

        function test_single_disk() {
            systemUsageLogic.disks = [{ used: 500, total: 1000 }];
            fuzzyCompare(systemUsageLogic.storagePercentage, 0.5, 0.001);
        }

        function test_multiple_disks() {
            systemUsageLogic.disks = [
                { used: 200, total: 1000 },
                { used: 300, total: 1000 }
            ];
            fuzzyCompare(systemUsageLogic.storagePercentage, 0.25, 0.001);
        }

        function test_empty_disks() {
            systemUsageLogic.disks = [];
            compare(systemUsageLogic.storagePercentage, 0);
        }

        function test_zero_total_size() {
            systemUsageLogic.disks = [{ used: 0, total: 0 }];
            compare(systemUsageLogic.storagePercentage, 0);
        }

        function test_full_disk() {
            systemUsageLogic.disks = [{ used: 500, total: 500 }];
            fuzzyCompare(systemUsageLogic.storagePercentage, 1.0, 0.001);
        }
    }
}
