pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

StyledRect {
    id: storageGaugeCardRoot

    property int currentDiskIndex: 0
    readonly property var currentDisk: SystemUsageService.disks.length > 0 ? SystemUsageService.disks[currentDiskIndex] : null
    property int diskCount: 0
    property real animatedPercentage: 0
    property color accentColor: Colours.palette.m3secondary

    color: Colours.tPalette.m3surfaceContainer
    radius: Appearance.rounding.large
    clip: true
    Component.onCompleted: {
        diskCount = SystemUsageService.disks.length;
        if (currentDisk)
            animatedPercentage = currentDisk.perc;
    }
    onCurrentDiskChanged: {
        if (currentDisk)
            animatedPercentage = currentDisk.perc;
    }

    Connections {
        function onDisksChanged() {
            if (SystemUsageService.disks.length !== storageGaugeCardRoot.diskCount)
                storageGaugeCardRoot.diskCount = SystemUsageService.disks.length;

            if (storageGaugeCardRoot.currentDisk)
                storageGaugeCardRoot.animatedPercentage = storageGaugeCardRoot.currentDisk.perc;
        }

        target: SystemUsageService
    }

    MouseArea {
        anchors.fill: parent
        onWheel: wheel => {
            if (wheel.angleDelta.y > 0)
                storageGaugeCardRoot.currentDiskIndex = (storageGaugeCardRoot.currentDiskIndex - 1 + storageGaugeCardRoot.diskCount) % storageGaugeCardRoot.diskCount;
            else if (wheel.angleDelta.y < 0)
                storageGaugeCardRoot.currentDiskIndex = (storageGaugeCardRoot.currentDiskIndex + 1) % storageGaugeCardRoot.diskCount;
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Appearance.padding.large
        spacing: Appearance.spacing.smaller

        PerformanceCardHeader {
            iconName: "hard_disk"
            title: {
                const base = "Storage";
                if (!storageGaugeCardRoot.currentDisk)
                    return base;

                return `${base} - ${storageGaugeCardRoot.currentDisk.mount}`;
            }
            accentColor: storageGaugeCardRoot.accentColor

            MaterialIcon {
                text: "unfold_more"
                color: Colours.palette.m3onSurfaceVariant
                font.pointSize: Appearance.font.size.normal
                visible: storageGaugeCardRoot.diskCount > 1
                opacity: 0.7
                ToolTip.visible: scrollHintHoverHandler.hovered
                ToolTip.text: "Scroll to switch disks"
                ToolTip.delay: 500

                HoverHandler {
                    id: scrollHintHoverHandler
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            PerformanceGaugeArc {
                anchors.centerIn: parent
                width: Math.min(parent.width, parent.height)
                height: width
                percentage: storageGaugeCardRoot.animatedPercentage
                accentColor: storageGaugeCardRoot.accentColor
            }

            StyledText {
                anchors.centerIn: parent
                text: storageGaugeCardRoot.currentDisk ? `${Math.round(storageGaugeCardRoot.currentDisk.perc * 100)}%` : "—"
                font.pointSize: Appearance.font.size.extraLarge
                font.weight: Font.Medium
                color: storageGaugeCardRoot.accentColor
            }
        }

        StyledText {
            Layout.alignment: Qt.AlignHCenter
            text: {
                if (!storageGaugeCardRoot.currentDisk)
                    return "—";

                const usedFormatted = SystemUsageService.formatKibibytes(storageGaugeCardRoot.currentDisk.used);
                const totalFormatted = SystemUsageService.formatKibibytes(storageGaugeCardRoot.currentDisk.total);
                return `${usedFormatted.value.toFixed(1)} / ${Math.floor(totalFormatted.value)} ${totalFormatted.unit}`;
            }
            font.pointSize: Appearance.font.size.smaller
            color: Colours.palette.m3onSurfaceVariant
        }
    }

    Behavior on animatedPercentage {
        Anim {
            duration: Appearance.anim.durations.large
        }
    }
}
