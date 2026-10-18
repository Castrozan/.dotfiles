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
            const query = process("nvidia-smi --query-gpu=utilization");
            query.stdout.read("38, 65\n");
            query.exited(0, 0);
            compare(observedUsage, 0.38);
            compare(observedTemperature, 65);
        }
        function test_nvidia_unavailable_usage() {
            graphics.gpuType = "NVIDIA";
            process("nvidia-smi --query-gpu=utilization").stdout.read("[N/A], [GPU requires reset]\n");
            verify(!Number.isFinite(observedUsage));
        }
        function test_nvidia_failed_query_clears_previous_usage_data() {
            return [
                {
                    tag: "command failure",
                    exitCode: 1,
                    exitStatus: 0
                },
                {
                    tag: "process crash",
                    exitCode: 0,
                    exitStatus: 1
                }
            ];
        }
        function test_nvidia_failed_query_clears_previous_usage(data) {
            graphics.gpuType = "NVIDIA";
            const query = process("nvidia-smi --query-gpu=utilization");
            query.stdout.read("38, 65\n");
            query.exited(data.exitCode, data.exitStatus);
            verify(!Number.isFinite(observedUsage));
            query.stdout.read("42, 65\n");
            compare(observedUsage, 0.42);
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
