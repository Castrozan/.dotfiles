pragma ComponentBehavior: Bound

import "performance"
import "../components"
import "../services"
import ".."
import QtQuick
import QtQuick.Layouts
import Quickshell.Services.UPower

Item {
    id: performanceTabRoot

    property bool dashboardIsActive: false

    function formatTemperatureDisplay(temperatureCelsius: real): string {
        return `${Math.ceil(DashboardConfig.useFahrenheitPerformance ? temperatureCelsius * 1.8 + 32 : temperatureCelsius)}°${DashboardConfig.useFahrenheitPerformance ? "F" : "C"}`;
    }

    implicitWidth: performanceContentRow.implicitWidth
    implicitHeight: performanceContentRow.implicitHeight

    StyledRect {
        id: noWidgetsPlaceholder

        color: Colours.tPalette.m3surfaceContainer
        visible: !DashboardConfig.performance.showCpu && !(DashboardConfig.performance.showGpu && SystemUsageService.gpuType !== "NONE") && !DashboardConfig.performance.showMemory && !DashboardConfig.performance.showStorage && !DashboardConfig.performance.showNetwork && !(UPower.displayDevice.isLaptopBattery && DashboardConfig.performance.showBattery)

        ColumnLayout {
            MaterialIcon {
                Layout.alignment: Qt.AlignHCenter
                text: "tune"
                font.pointSize: Appearance.font.size.extraLarge * 2
                color: Colours.palette.m3onSurfaceVariant
            }

            StyledText {
                Layout.alignment: Qt.AlignHCenter
                text: "No widgets enabled"
                font.pointSize: Appearance.font.size.large
                color: Colours.palette.m3onSurface
            }

            StyledText {
                Layout.alignment: Qt.AlignHCenter
                text: "Enable widgets in dashboard settings"
                font.pointSize: Appearance.font.size.small
                color: Colours.palette.m3onSurfaceVariant
            }
        }
    }

    RowLayout {
        id: performanceContentRow

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Appearance.spacing.normal
        visible: !noWidgetsPlaceholder.visible

        Component.onDestruction: {
            if (performanceTabRoot.dashboardIsActive)
                SystemUsageService.refCount--;
        }

        Connections {
            target: performanceTabRoot
            function onDashboardIsActiveChanged() {
                if (performanceTabRoot.dashboardIsActive)
                    SystemUsageService.refCount++;
                else
                    SystemUsageService.refCount--;
            }
        }

        ColumnLayout {
            id: performanceMainColumn
            spacing: Appearance.spacing.normal

            RowLayout {
                Layout.fillWidth: true
                spacing: Appearance.spacing.normal
                visible: DashboardConfig.performance.showCpu || (DashboardConfig.performance.showGpu && SystemUsageService.gpuType !== "NONE")

                PerformanceHeroCard {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 400
                    Layout.preferredHeight: 150
                    visible: DashboardConfig.performance.showCpu
                    iconName: "memory"
                    title: SystemUsageService.cpuName ? `CPU - ${SystemUsageService.cpuName}` : "CPU"
                    mainValue: `${Math.round(SystemUsageService.cpuPercentage * 100)}%`
                    mainLabel: "Usage"
                    secondaryValue: performanceTabRoot.formatTemperatureDisplay(SystemUsageService.cpuTemperature)
                    secondaryLabel: "Temp"
                    usage: SystemUsageService.cpuPercentage
                    temperature: SystemUsageService.cpuTemperature
                    accentColor: Colours.palette.m3primary
                }

                PerformanceHeroCard {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 400
                    Layout.preferredHeight: 150
                    visible: DashboardConfig.performance.showGpu && SystemUsageService.gpuType !== "NONE"
                    iconName: "desktop_windows"
                    title: SystemUsageService.gpuName ? `GPU - ${SystemUsageService.gpuName}` : "GPU"
                    mainValue: `${Math.round(SystemUsageService.gpuPercentage * 100)}%`
                    mainLabel: "Usage"
                    secondaryValue: performanceTabRoot.formatTemperatureDisplay(SystemUsageService.gpuTemperature)
                    secondaryLabel: "Temp"
                    usage: SystemUsageService.gpuPercentage
                    temperature: SystemUsageService.gpuTemperature
                    accentColor: Colours.palette.m3secondary
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: Appearance.spacing.normal
                visible: DashboardConfig.performance.showMemory || DashboardConfig.performance.showStorage || DashboardConfig.performance.showNetwork

                PerformanceGaugeCard {
                    Layout.minimumWidth: 250
                    Layout.preferredHeight: 220
                    Layout.fillWidth: !DashboardConfig.performance.showStorage && !DashboardConfig.performance.showNetwork
                    iconName: "memory_alt"
                    title: "Memory"
                    percentage: SystemUsageService.memoryPercentage
                    subtitle: {
                        const usedFormatted = SystemUsageService.formatKibibytes(SystemUsageService.memoryUsedKib);
                        const totalFormatted = SystemUsageService.formatKibibytes(SystemUsageService.memoryTotalKib);
                        return `${usedFormatted.value.toFixed(1)} / ${Math.floor(totalFormatted.value)} ${totalFormatted.unit}`;
                    }
                    accentColor: Colours.palette.m3tertiary
                    visible: DashboardConfig.performance.showMemory
                }

                PerformanceStorageGaugeCard {
                    Layout.minimumWidth: 250
                    Layout.preferredHeight: 220
                    Layout.fillWidth: !DashboardConfig.performance.showNetwork
                    visible: DashboardConfig.performance.showStorage
                }

                PerformanceNetworkCard {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 200
                    Layout.preferredHeight: 220
                    visible: DashboardConfig.performance.showNetwork
                    dashboardIsActive: performanceTabRoot.dashboardIsActive
                }
            }
        }

        PerformanceBatteryTank {
            Layout.preferredWidth: 120
            Layout.preferredHeight: performanceMainColumn.implicitHeight
            visible: UPower.displayDevice.isLaptopBattery && DashboardConfig.performance.showBattery
        }
    }
}
