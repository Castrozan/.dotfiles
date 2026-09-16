import QtQuick
import QtTest

SystemUsageFixture {
    id: root

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
}
