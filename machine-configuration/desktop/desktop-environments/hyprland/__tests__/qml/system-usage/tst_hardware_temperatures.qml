import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/services/system-usage"

Item {
    property real cpuTemperature: -1
    property real gpuTemperature: -1
    HardwareTemperatures {
        id: temperatures
        gpuType: "GENERIC"
        onCpuTemperatureRead: temperature => cpuTemperature = temperature
        onGpuTemperatureRead: temperature => gpuTemperature = temperature
    }
    TestCase {
        name: "HardwareTemperatures"
        function test_package_temperature() {
            temperatures.stdout.read("Package id 0: +55.5°C\n");
            compare(cpuTemperature, 55.5);
        }
        function test_amd_fallback_temperature() {
            temperatures.stdout.read("Tctl: +61.2°C\n");
            compare(cpuTemperature, 61.2);
        }
        function test_pci_adapter_average() {
            temperatures.gpuType = "GENERIC";
            temperatures.stdout.read("Adapter: PCI adapter\nedge: +40.0°C\njunction: +60.0°C\n\nAdapter: ISA adapter\ntemp1: +90.0°C\n");
            compare(gpuTemperature, 50);
        }
        function test_nvidia_temperature_comes_from_gpu_query() {
            temperatures.gpuType = "NVIDIA";
            gpuTemperature = 73;
            temperatures.stdout.read("Adapter: PCI adapter\nedge: +40.0°C\n");
            compare(gpuTemperature, 73);
        }
    }
}
