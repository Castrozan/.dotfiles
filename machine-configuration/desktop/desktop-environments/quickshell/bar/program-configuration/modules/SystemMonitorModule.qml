import QtQuick
import QtQuick.Layouts
import Quickshell.Io
import ".."
import "../dashboard/services/system-usage"

ColumnLayout {
    id: systemMonitorModuleRoot

    spacing: 0

    property real cpuPercentage: 0
    property real memoryPercentage: 0
    property string gpuType: "NONE"
    property real gpuPercentage: NaN
    property real previousCpuIdle: 0
    property real previousCpuTotal: 0

    Timer {
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            cpuStatFileView.reload();
            memInfoFileView.reload();
            if (systemMonitorModuleRoot.gpuType !== "NONE")
                graphicsUsage.refresh();
        }
    }

    GraphicsUsage {
        id: graphicsUsage

        gpuType: systemMonitorModuleRoot.gpuType
        Component.onCompleted: detect()
        onTypeDiscovered: type => {
            systemMonitorModuleRoot.gpuType = type;
            if (type !== "NONE")
                refresh();
        }
        onUsageDiscovered: percentage => systemMonitorModuleRoot.gpuPercentage = percentage
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
                const totalDiff = total - systemMonitorModuleRoot.previousCpuTotal;
                const idleDiff = idle - systemMonitorModuleRoot.previousCpuIdle;
                systemMonitorModuleRoot.cpuPercentage = totalDiff > 0 ? (1 - idleDiff / totalDiff) : 0;
                systemMonitorModuleRoot.previousCpuTotal = total;
                systemMonitorModuleRoot.previousCpuIdle = idle;
            }
        }
    }

    FileView {
        id: memInfoFileView

        path: "/proc/meminfo"
        onLoaded: {
            const data = text();
            const totalMatch = data.match(/MemTotal:\s*(\d+)/);
            const availableMatch = data.match(/MemAvailable:\s*(\d+)/);
            if (totalMatch && availableMatch) {
                const total = parseInt(totalMatch[1], 10) || 1;
                const available = parseInt(availableMatch[1], 10) || 0;
                systemMonitorModuleRoot.memoryPercentage = (total - available) / total;
            }
        }
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: "CPU"
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: Math.round(systemMonitorModuleRoot.cpuPercentage * 100) + "%"
        font.pixelSize: 16
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    Rectangle {
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        width: 20
        height: 1
        color: ThemeColors.dim
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: "RAM"
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    Text {
        Layout.alignment: Qt.AlignHCenter
        text: Math.round(systemMonitorModuleRoot.memoryPercentage * 100) + "%"
        font.pixelSize: 16
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    Rectangle {
        visible: systemMonitorModuleRoot.gpuType !== "NONE"
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        width: 20
        height: 1
        color: ThemeColors.dim
    }

    Text {
        visible: systemMonitorModuleRoot.gpuType !== "NONE"
        Layout.alignment: Qt.AlignHCenter
        text: "GPU"
        font.pixelSize: 14
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }

    Text {
        visible: systemMonitorModuleRoot.gpuType !== "NONE"
        Layout.alignment: Qt.AlignHCenter
        text: Number.isFinite(systemMonitorModuleRoot.gpuPercentage) ? Math.round(systemMonitorModuleRoot.gpuPercentage * 100) + "%" : "N/A"
        font.pixelSize: 16
        font.bold: true
        font.family: "JetBrainsMono Nerd Font"
        color: ThemeColors.foreground
    }
}
