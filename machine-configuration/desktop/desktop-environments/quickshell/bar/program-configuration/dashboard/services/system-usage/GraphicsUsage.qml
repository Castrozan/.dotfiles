import Quickshell
import Quickshell.Io

Scope {
    id: graphicsUsageRoot

    required property string gpuType

    signal nameDiscovered(string name)
    signal typeDiscovered(string type)
    signal usageDiscovered(real percentage)
    signal temperatureDiscovered(real temperature)

    function detect(): void {
        gpuNameDetectionProcess.running = true;
        gpuTypeDetectionProcess.running = true;
    }

    function refresh(): void {
        gpuUsageProcess.running = true;
    }

    function cleanGpuName(rawName: string): string {
        return rawName.replace(/NVIDIA GeForce /gi, "").replace(/NVIDIA /gi, "").replace(/AMD Radeon /gi, "").replace(/AMD /gi, "").replace(/Intel /gi, "").replace(/\(R\)/gi, "").replace(/\(TM\)/gi, "").replace(/Graphics/gi, "").replace(/\s+/g, " ").trim();
    }

    Process {
        id: gpuNameDetectionProcess

        running: false
        command: ["sh", "-c", "nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || lspci 2>/dev/null | grep -i 'vga\\|3d\\|display' | head -1"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                const output = data.trim();
                if (!output)
                    return;

                if (output.toLowerCase().includes("nvidia") || output.toLowerCase().includes("geforce") || output.toLowerCase().includes("rtx") || output.toLowerCase().includes("gtx")) {
                    graphicsUsageRoot.nameDiscovered(graphicsUsageRoot.cleanGpuName(output));
                } else {
                    const bracketMatch = output.match(/\[([^\]]+)\]/);
                    if (bracketMatch)
                        graphicsUsageRoot.nameDiscovered(graphicsUsageRoot.cleanGpuName(bracketMatch[1]));
                    else {
                        const colonMatch = output.match(/:\s*(.+)/);
                        if (colonMatch)
                            graphicsUsageRoot.nameDiscovered(graphicsUsageRoot.cleanGpuName(colonMatch[1]));
                    }
                }
            }
        }
    }

    Process {
        id: gpuTypeDetectionProcess

        running: false
        command: ["sh", "-c", "if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then echo NVIDIA; elif ls /sys/class/drm/card*/device/gpu_busy_percent 2>/dev/null | grep -q .; then echo GENERIC; else echo NONE; fi"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => graphicsUsageRoot.typeDiscovered(data.trim())
        }
    }

    Process {
        id: gpuUsageProcess

        command: graphicsUsageRoot.gpuType === "GENERIC" ? ["sh", "-c", "cat /sys/class/drm/card*/device/gpu_busy_percent 2>/dev/null || echo 0"] : graphicsUsageRoot.gpuType === "NVIDIA" ? ["sh", "-c", "nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,noheader,nounits 2>/dev/null || echo '0, 0'"] : ["echo"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                if (graphicsUsageRoot.gpuType === "GENERIC") {
                    const percentages = data.trim().split("\n");
                    const sum = percentages.reduce((acc, d) => acc + parseInt(d, 10), 0);
                    graphicsUsageRoot.usageDiscovered(sum / percentages.length / 100);
                } else if (graphicsUsageRoot.gpuType === "NVIDIA") {
                    const [usage, temp] = data.trim().split(",");
                    graphicsUsageRoot.usageDiscovered(parseInt(usage, 10) / 100);
                    graphicsUsageRoot.temperatureDiscovered(parseInt(temp, 10));
                } else {
                    graphicsUsageRoot.usageDiscovered(0);
                    graphicsUsageRoot.temperatureDiscovered(0);
                }
            }
        }
    }
}
