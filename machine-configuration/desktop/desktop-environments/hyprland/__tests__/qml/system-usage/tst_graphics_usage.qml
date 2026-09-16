import QtQuick
import QtTest
import "../../../../quickshell/bar/program-configuration/dashboard/services/system-usage"

Item {
    property string observedName: ""
    property string observedType: ""
    property real observedUsage: -1
    property real observedTemperature: -1

    GraphicsUsage {
        id: graphics
        gpuType: "NVIDIA"
        onNameDiscovered: name => observedName = name
        onTypeDiscovered: type => observedType = type
        onUsageDiscovered: percentage => observedUsage = percentage
        onTemperatureDiscovered: temperature => observedTemperature = temperature
    }

    TestCase {
        name: "GraphicsUsage"
        function process(commandPrefix) {
            for (const candidate of graphics.children)
                if (candidate.command.join(" ").startsWith(commandPrefix))
                    return candidate;
            fail("Missing graphics command: " + commandPrefix);
        }
        function test_gpu_name_detection() {
            process("sh -c nvidia-smi --query-gpu=name").stdout.read("NVIDIA GeForce RTX 4090\n");
            compare(observedName, "RTX 4090");
            process("sh -c nvidia-smi --query-gpu=name").stdout.read("03:00.0 VGA controller: AMD [Radeon RX 7900 Graphics]");
            compare(observedName, "Radeon RX 7900");
        }
        function test_detected_type_is_trimmed() {
            process("sh -c if command").stdout.read("GENERIC\n");
            compare(observedType, "GENERIC");
        }
        function test_nvidia_usage_and_temperature() {
            graphics.gpuType = "NVIDIA";
            process("sh -c nvidia-smi --query-gpu=utilization").stdout.read("38, 65\n");
            compare(observedUsage, 0.38);
            compare(observedTemperature, 65);
        }
        function test_generic_usage_averages_devices() {
            graphics.gpuType = "GENERIC";
            process("sh -c cat /sys").stdout.read("20\n80\n");
            compare(observedUsage, 0.5);
        }
        function test_absent_gpu_resets_usage_and_temperature() {
            graphics.gpuType = "NONE";
            process("echo").stdout.read("");
            compare(observedUsage, 0);
            compare(observedTemperature, 0);
        }
    }
}
