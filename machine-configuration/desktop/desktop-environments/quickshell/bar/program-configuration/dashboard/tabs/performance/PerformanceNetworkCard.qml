pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Layouts

StyledRect {
    id: networkCardRoot

    property bool dashboardIsActive: false
    property color accentColor: Colours.palette.m3primary

    color: Colours.tPalette.m3surfaceContainer
    radius: Appearance.rounding.large
    clip: true

    Component.onDestruction: {
        if (networkCardRoot.dashboardIsActive)
            NetworkUsageService.refCount--;
    }

    Connections {
        target: networkCardRoot
        function onDashboardIsActiveChanged() {
            if (networkCardRoot.dashboardIsActive)
                NetworkUsageService.refCount++;
            else
                NetworkUsageService.refCount--;
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Appearance.padding.large
        spacing: Appearance.spacing.small

        PerformanceCardHeader {
            iconName: "swap_vert"
            title: "Network"
            accentColor: networkCardRoot.accentColor
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            PerformanceNetworkSparkline {
                anchors.fill: parent
                dashboardIsActive: networkCardRoot.dashboardIsActive
            }

            StyledText {
                anchors.centerIn: parent
                text: "Collecting data..."
                font.pointSize: Appearance.font.size.small
                color: Colours.palette.m3onSurfaceVariant
                visible: NetworkUsageService.downloadHistory.length < 2
                opacity: 0.6
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Appearance.spacing.normal

            MaterialIcon {
                text: "download"
                color: Colours.palette.m3tertiary
                font.pointSize: Appearance.font.size.normal
            }

            StyledText {
                text: "Download"
                font.pointSize: Appearance.font.size.small
                color: Colours.palette.m3onSurfaceVariant
            }

            Item {
                Layout.fillWidth: true
            }

            StyledText {
                text: {
                    const formatted = NetworkUsageService.formatBytesPerSecond(NetworkUsageService.downloadSpeed ?? 0);
                    return formatted ? `${formatted.value.toFixed(1)} ${formatted.unit}` : "0.0 B/s";
                }
                font.pointSize: Appearance.font.size.normal
                font.weight: Font.Medium
                color: Colours.palette.m3tertiary
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Appearance.spacing.normal

            MaterialIcon {
                text: "upload"
                color: Colours.palette.m3secondary
                font.pointSize: Appearance.font.size.normal
            }

            StyledText {
                text: "Upload"
                font.pointSize: Appearance.font.size.small
                color: Colours.palette.m3onSurfaceVariant
            }

            Item {
                Layout.fillWidth: true
            }

            StyledText {
                text: {
                    const formatted = NetworkUsageService.formatBytesPerSecond(NetworkUsageService.uploadSpeed ?? 0);
                    return formatted ? `${formatted.value.toFixed(1)} ${formatted.unit}` : "0.0 B/s";
                }
                font.pointSize: Appearance.font.size.normal
                font.weight: Font.Medium
                color: Colours.palette.m3secondary
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Appearance.spacing.normal

            MaterialIcon {
                text: "history"
                color: Colours.palette.m3onSurfaceVariant
                font.pointSize: Appearance.font.size.normal
            }

            StyledText {
                text: "Total"
                font.pointSize: Appearance.font.size.small
                color: Colours.palette.m3onSurfaceVariant
            }

            Item {
                Layout.fillWidth: true
            }

            StyledText {
                text: {
                    const downloadFormatted = NetworkUsageService.formatBytesTotal(NetworkUsageService.downloadTotal ?? 0);
                    const uploadFormatted = NetworkUsageService.formatBytesTotal(NetworkUsageService.uploadTotal ?? 0);
                    return (downloadFormatted && uploadFormatted) ? `↓${downloadFormatted.value.toFixed(1)}${downloadFormatted.unit} ↑${uploadFormatted.value.toFixed(1)}${uploadFormatted.unit}` : "↓0.0B ↑0.0B";
                }
                font.pointSize: Appearance.font.size.small
                color: Colours.palette.m3onSurfaceVariant
            }
        }
    }
}
