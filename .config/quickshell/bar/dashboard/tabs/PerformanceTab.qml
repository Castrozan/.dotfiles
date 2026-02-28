pragma ComponentBehavior: Bound

import "../components"
import "../services"
import ".."
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell.Services.UPower

Item {
    id: performanceTabRoot

    readonly property int performanceMinWidth: 500

    function formatTemperatureDisplay(temperatureCelsius: real): string {
        return `${Math.ceil(DashboardConfig.useFahrenheitPerformance ? temperatureCelsius * 1.8 + 32 : temperatureCelsius)}\u00B0${DashboardConfig.useFahrenheitPerformance ? "F" : "C"}`;
    }

    implicitWidth: 800
    implicitHeight: 400

    StyledRect {
        id: noWidgetsPlaceholder

        anchors.centerIn: parent
        width: 400
        height: 100
        radius: Appearance.rounding.large
        color: Colours.tPalette.m3surfaceContainer
        visible: !DashboardConfig.performance.showCpu && !(DashboardConfig.performance.showGpu && SystemUsageService.gpuType !== "NONE") && !DashboardConfig.performance.showMemory && !DashboardConfig.performance.showStorage && !DashboardConfig.performance.showNetwork && !(UPower.displayDevice.isLaptopBattery && DashboardConfig.performance.showBattery)

        ColumnLayout {
            anchors.centerIn: parent
            spacing: Appearance.spacing.normal

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

        Component.onCompleted: SystemUsageService.refCount++
        Component.onDestruction: SystemUsageService.refCount--

        ColumnLayout {
            id: performanceMainColumn

            Layout.fillWidth: true
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
                }
            }
        }

        PerformanceBatteryTank {
            Layout.preferredWidth: 120
            Layout.preferredHeight: performanceMainColumn.implicitHeight
            visible: UPower.displayDevice.isLaptopBattery && DashboardConfig.performance.showBattery
        }
    }

    component PerformanceCardHeader: RowLayout {
        property string iconName
        property string title
        property color accentColor: Colours.palette.m3primary

        Layout.fillWidth: true
        spacing: Appearance.spacing.small

        MaterialIcon {
            text: parent.iconName
            fill: 1
            color: parent.accentColor
            font.pointSize: Appearance.spacing.large
        }

        StyledText {
            Layout.fillWidth: true
            text: parent.title
            font.pointSize: Appearance.font.size.normal
            elide: Text.ElideRight
        }
    }

    component PerformanceProgressBar: StyledRect {
        id: performanceProgressBarRoot

        property real value: 0
        property color foregroundColor: Colours.palette.m3primary
        property color backgroundColor: Colours.layer(Colours.palette.m3surfaceContainerHigh, 2)
        property real animatedValue: 0

        color: backgroundColor
        radius: Appearance.rounding.full
        Component.onCompleted: animatedValue = value
        onValueChanged: animatedValue = value

        StyledRect {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: parent.width * performanceProgressBarRoot.animatedValue
            color: performanceProgressBarRoot.foregroundColor
            radius: Appearance.rounding.full
        }

        Behavior on animatedValue {
            Anim {
                duration: Appearance.anim.durations.large
            }
        }
    }

    component PerformanceHeroCard: StyledClippingRect {
        id: performanceHeroCardRoot

        property string iconName
        property string title
        property string mainValue
        property string mainLabel
        property string secondaryValue
        property string secondaryLabel
        property real usage: 0
        property real temperature: 0
        property color accentColor: Colours.palette.m3primary
        readonly property real maximumTemperature: 100
        readonly property real temperatureProgress: Math.min(1, Math.max(0, temperature / maximumTemperature))
        property real animatedUsage: 0
        property real animatedTemperature: 0

        color: Colours.tPalette.m3surfaceContainer
        radius: Appearance.rounding.large
        Component.onCompleted: {
            animatedUsage = usage;
            animatedTemperature = temperatureProgress;
        }
        onUsageChanged: animatedUsage = usage
        onTemperatureProgressChanged: animatedTemperature = temperatureProgress

        StyledRect {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: parent.width * performanceHeroCardRoot.animatedUsage
            color: Qt.alpha(performanceHeroCardRoot.accentColor, 0.15)
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: Appearance.padding.large
            anchors.rightMargin: Appearance.padding.large
            anchors.topMargin: Appearance.padding.normal
            anchors.bottomMargin: Appearance.padding.normal
            spacing: Appearance.spacing.small

            PerformanceCardHeader {
                iconName: performanceHeroCardRoot.iconName
                title: performanceHeroCardRoot.title
                accentColor: performanceHeroCardRoot.accentColor
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: Appearance.spacing.normal

                Column {
                    Layout.alignment: Qt.AlignBottom
                    Layout.fillWidth: true
                    spacing: Appearance.spacing.small

                    Row {
                        spacing: Appearance.spacing.small

                        StyledText {
                            text: performanceHeroCardRoot.secondaryValue
                            font.pointSize: Appearance.font.size.normal
                            font.weight: Font.Medium
                        }

                        StyledText {
                            text: performanceHeroCardRoot.secondaryLabel
                            font.pointSize: Appearance.font.size.small
                            color: Colours.palette.m3onSurfaceVariant
                            anchors.baseline: parent.children[0].baseline
                        }
                    }

                    PerformanceProgressBar {
                        width: parent.width * 0.5
                        height: 6
                        value: performanceHeroCardRoot.temperatureProgress
                        foregroundColor: performanceHeroCardRoot.accentColor
                        backgroundColor: Qt.alpha(performanceHeroCardRoot.accentColor, 0.2)
                    }
                }

                Item {
                    Layout.fillWidth: true
                }
            }
        }

        Column {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.margins: Appearance.padding.large
            anchors.rightMargin: 32
            spacing: 0

            StyledText {
                anchors.right: parent.right
                text: performanceHeroCardRoot.mainLabel
                font.pointSize: Appearance.font.size.normal
                color: Colours.palette.m3onSurfaceVariant
            }

            StyledText {
                anchors.right: parent.right
                text: performanceHeroCardRoot.mainValue
                font.pointSize: Appearance.font.size.extraLarge
                font.weight: Font.Medium
                color: performanceHeroCardRoot.accentColor
            }
        }

        Behavior on animatedUsage {
            Anim {
                duration: Appearance.anim.durations.large
            }
        }

        Behavior on animatedTemperature {
            Anim {
                duration: Appearance.anim.durations.large
            }
        }
    }

    component PerformanceGaugeCard: StyledRect {
        id: performanceGaugeCardRoot

        property string iconName
        property string title
        property real percentage: 0
        property string subtitle
        property color accentColor: Colours.palette.m3primary
        readonly property real gaugeArcStartAngle: 0.75 * Math.PI
        readonly property real gaugeArcSweepAngle: 1.5 * Math.PI
        property real animatedPercentage: 0

        color: Colours.tPalette.m3surfaceContainer
        radius: Appearance.rounding.large
        clip: true
        Component.onCompleted: animatedPercentage = percentage
        onPercentageChanged: animatedPercentage = percentage

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Appearance.padding.large
            spacing: Appearance.spacing.smaller

            PerformanceCardHeader {
                iconName: performanceGaugeCardRoot.iconName
                title: performanceGaugeCardRoot.title
                accentColor: performanceGaugeCardRoot.accentColor
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                Canvas {
                    id: gaugeArcCanvas

                    anchors.centerIn: parent
                    width: Math.min(parent.width, parent.height)
                    height: width
                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.reset();
                        const centerX = width / 2;
                        const centerY = height / 2;
                        const arcRadius = (Math.min(width, height) - 12) / 2;
                        const lineWidth = 10;
                        ctx.beginPath();
                        ctx.arc(centerX, centerY, arcRadius, performanceGaugeCardRoot.gaugeArcStartAngle, performanceGaugeCardRoot.gaugeArcStartAngle + performanceGaugeCardRoot.gaugeArcSweepAngle);
                        ctx.lineWidth = lineWidth;
                        ctx.lineCap = "round";
                        ctx.strokeStyle = Colours.layer(Colours.palette.m3surfaceContainerHigh, 2);
                        ctx.stroke();
                        if (performanceGaugeCardRoot.animatedPercentage > 0) {
                            ctx.beginPath();
                            ctx.arc(centerX, centerY, arcRadius, performanceGaugeCardRoot.gaugeArcStartAngle, performanceGaugeCardRoot.gaugeArcStartAngle + performanceGaugeCardRoot.gaugeArcSweepAngle * performanceGaugeCardRoot.animatedPercentage);
                            ctx.lineWidth = lineWidth;
                            ctx.lineCap = "round";
                            ctx.strokeStyle = performanceGaugeCardRoot.accentColor;
                            ctx.stroke();
                        }
                    }
                    Component.onCompleted: requestPaint()

                    Connections {
                        function onAnimatedPercentageChanged() {
                            gaugeArcCanvas.requestPaint();
                        }

                        target: performanceGaugeCardRoot
                    }

                    Connections {
                        function onPaletteChanged() {
                            gaugeArcCanvas.requestPaint();
                        }

                        target: Colours
                    }
                }

                StyledText {
                    anchors.centerIn: parent
                    text: `${Math.round(performanceGaugeCardRoot.percentage * 100)}%`
                    font.pointSize: Appearance.font.size.extraLarge
                    font.weight: Font.Medium
                    color: performanceGaugeCardRoot.accentColor
                }
            }

            StyledText {
                Layout.alignment: Qt.AlignHCenter
                text: performanceGaugeCardRoot.subtitle
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

    component PerformanceStorageGaugeCard: StyledRect {
        id: storageGaugeCardRoot

        property int currentDiskIndex: 0
        readonly property var currentDisk: SystemUsageService.disks.length > 0 ? SystemUsageService.disks[currentDiskIndex] : null
        property int diskCount: 0
        readonly property real storageArcStartAngle: 0.75 * Math.PI
        readonly property real storageArcSweepAngle: 1.5 * Math.PI
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

                Canvas {
                    id: storageGaugeArcCanvas

                    anchors.centerIn: parent
                    width: Math.min(parent.width, parent.height)
                    height: width
                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.reset();
                        const centerX = width / 2;
                        const centerY = height / 2;
                        const arcRadius = (Math.min(width, height) - 12) / 2;
                        const lineWidth = 10;
                        ctx.beginPath();
                        ctx.arc(centerX, centerY, arcRadius, storageGaugeCardRoot.storageArcStartAngle, storageGaugeCardRoot.storageArcStartAngle + storageGaugeCardRoot.storageArcSweepAngle);
                        ctx.lineWidth = lineWidth;
                        ctx.lineCap = "round";
                        ctx.strokeStyle = Colours.layer(Colours.palette.m3surfaceContainerHigh, 2);
                        ctx.stroke();
                        if (storageGaugeCardRoot.animatedPercentage > 0) {
                            ctx.beginPath();
                            ctx.arc(centerX, centerY, arcRadius, storageGaugeCardRoot.storageArcStartAngle, storageGaugeCardRoot.storageArcStartAngle + storageGaugeCardRoot.storageArcSweepAngle * storageGaugeCardRoot.animatedPercentage);
                            ctx.lineWidth = lineWidth;
                            ctx.lineCap = "round";
                            ctx.strokeStyle = storageGaugeCardRoot.accentColor;
                            ctx.stroke();
                        }
                    }
                    Component.onCompleted: requestPaint()

                    Connections {
                        function onAnimatedPercentageChanged() {
                            storageGaugeArcCanvas.requestPaint();
                        }

                        target: storageGaugeCardRoot
                    }

                    Connections {
                        function onPaletteChanged() {
                            storageGaugeArcCanvas.requestPaint();
                        }

                        target: Colours
                    }
                }

                StyledText {
                    anchors.centerIn: parent
                    text: storageGaugeCardRoot.currentDisk ? `${Math.round(storageGaugeCardRoot.currentDisk.perc * 100)}%` : "\u2014"
                    font.pointSize: Appearance.font.size.extraLarge
                    font.weight: Font.Medium
                    color: storageGaugeCardRoot.accentColor
                }
            }

            StyledText {
                Layout.alignment: Qt.AlignHCenter
                text: {
                    if (!storageGaugeCardRoot.currentDisk)
                        return "\u2014";

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

    component PerformanceNetworkCard: StyledRect {
        id: networkCardRoot

        property color accentColor: Colours.palette.m3primary

        color: Colours.tPalette.m3surfaceContainer
        radius: Appearance.rounding.large
        clip: true

        Component.onCompleted: NetworkUsageService.refCount++
        Component.onDestruction: NetworkUsageService.refCount--

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

                Canvas {
                    id: networkSparklineCanvas

                    property var downloadHistoryData: NetworkUsageService.downloadHistory
                    property var uploadHistoryData: NetworkUsageService.uploadHistory
                    property real targetMaximum: 1024
                    property real smoothedMaximum: targetMaximum
                    property real slideAnimationProgress: 0
                    property int internalTickCount: 0
                    property int lastProcessedTickCount: -1

                    function checkAndAnimateSparkline(): void {
                        const currentLength = (downloadHistoryData || []).length;
                        if (currentLength > 0 && internalTickCount !== lastProcessedTickCount) {
                            lastProcessedTickCount = internalTickCount;
                            updateSparklineMaximum();
                        }
                    }

                    function updateSparklineMaximum(): void {
                        const downloadHistoryArray = downloadHistoryData || [];
                        const uploadHistoryArray = uploadHistoryData || [];
                        const allValues = downloadHistoryArray.concat(uploadHistoryArray);
                        targetMaximum = Math.max(...allValues, 1024);
                        requestPaint();
                    }

                    anchors.fill: parent
                    onDownloadHistoryDataChanged: checkAndAnimateSparkline()
                    onUploadHistoryDataChanged: checkAndAnimateSparkline()
                    onSmoothedMaximumChanged: requestPaint()
                    onSlideAnimationProgressChanged: requestPaint()

                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.reset();
                        const canvasWidth = width;
                        const canvasHeight = height;
                        const downloadHistoryArray = downloadHistoryData || [];
                        const uploadHistoryArray = uploadHistoryData || [];
                        if (downloadHistoryArray.length < 2 && uploadHistoryArray.length < 2)
                            return;

                        const maximumValue = smoothedMaximum;

                        const drawSparkline = (historyData, strokeColor, fillAlpha) => {
                            if (historyData.length < 2)
                                return;

                            const dataLength = historyData.length;
                            const stepWidth = canvasWidth / (NetworkUsageService.historyLength - 1);
                            const startXPosition = canvasWidth - (dataLength - 1) * stepWidth - stepWidth * slideAnimationProgress + stepWidth;
                            ctx.beginPath();
                            ctx.moveTo(startXPosition, canvasHeight - (historyData[0] / maximumValue) * canvasHeight);
                            for (let i = 1; i < dataLength; i++) {
                                const pointX = startXPosition + i * stepWidth;
                                const pointY = canvasHeight - (historyData[i] / maximumValue) * canvasHeight;
                                ctx.lineTo(pointX, pointY);
                            }
                            ctx.strokeStyle = strokeColor;
                            ctx.lineWidth = 2;
                            ctx.lineCap = "round";
                            ctx.lineJoin = "round";
                            ctx.stroke();
                            ctx.lineTo(startXPosition + (dataLength - 1) * stepWidth, canvasHeight);
                            ctx.lineTo(startXPosition, canvasHeight);
                            ctx.closePath();
                            ctx.fillStyle = Qt.rgba(Qt.color(strokeColor).r, Qt.color(strokeColor).g, Qt.color(strokeColor).b, fillAlpha);
                            ctx.fill();
                        };

                        drawSparkline(uploadHistoryArray, Colours.palette.m3secondary.toString(), 0.15);
                        drawSparkline(downloadHistoryArray, Colours.palette.m3tertiary.toString(), 0.2);
                    }

                    Component.onCompleted: updateSparklineMaximum()

                    Connections {
                        function onPaletteChanged() {
                            networkSparklineCanvas.requestPaint();
                        }

                        target: Colours
                    }

                    Timer {
                        interval: DashboardConfig.resourceUpdateInterval
                        running: true
                        repeat: true
                        onTriggered: networkSparklineCanvas.internalTickCount++
                    }

                    NumberAnimation on slideAnimationProgress {
                        from: 0
                        to: 1
                        duration: DashboardConfig.resourceUpdateInterval
                        loops: Animation.Infinite
                        running: true
                    }

                    Behavior on smoothedMaximum {
                        Anim {
                            duration: Appearance.anim.durations.large
                        }
                    }
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
                        return (downloadFormatted && uploadFormatted) ? `\u2193${downloadFormatted.value.toFixed(1)}${downloadFormatted.unit} \u2191${uploadFormatted.value.toFixed(1)}${uploadFormatted.unit}` : "\u21930.0B \u21910.0B";
                    }
                    font.pointSize: Appearance.font.size.small
                    color: Colours.palette.m3onSurfaceVariant
                }
            }
        }
    }

    component PerformanceBatteryTank: StyledClippingRect {
        id: batteryTankRoot

        property real batteryPercentage: UPower.displayDevice.percentage
        property bool isBatteryCharging: UPower.displayDevice.state === UPowerDeviceState.Charging
        property color batteryAccentColor: Colours.palette.m3primary
        property real animatedBatteryPercentage: 0

        color: Colours.tPalette.m3surfaceContainer
        radius: Appearance.rounding.large
        Component.onCompleted: animatedBatteryPercentage = batteryPercentage
        onBatteryPercentageChanged: animatedBatteryPercentage = batteryPercentage

        StyledRect {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: parent.height * batteryTankRoot.animatedBatteryPercentage
            color: Qt.alpha(batteryTankRoot.batteryAccentColor, 0.15)
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Appearance.padding.large
            spacing: Appearance.spacing.small

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Appearance.spacing.small

                MaterialIcon {
                    text: {
                        if (!UPower.displayDevice.isLaptopBattery)
                            return "balance";

                        if (UPower.displayDevice.state === UPowerDeviceState.FullyCharged)
                            return "battery_full";

                        const percentage = UPower.displayDevice.percentage;
                        const isCharging = [UPowerDeviceState.Charging, UPowerDeviceState.PendingCharge].includes(UPower.displayDevice.state);
                        if (percentage >= 0.99)
                            return "battery_full";

                        let batteryLevel = Math.floor(percentage * 7);
                        if (isCharging && (batteryLevel === 4 || batteryLevel === 1))
                            batteryLevel--;

                        return isCharging ? `battery_charging_${(batteryLevel + 3) * 10}` : `battery_${batteryLevel}_bar`;
                    }
                    font.pointSize: Appearance.font.size.large
                    color: batteryTankRoot.batteryAccentColor
                }

                StyledText {
                    Layout.fillWidth: true
                    text: "Battery"
                    font.pointSize: Appearance.font.size.normal
                    color: Colours.palette.m3onSurface
                }
            }

            Item {
                Layout.fillHeight: true
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: -4

                StyledText {
                    Layout.alignment: Qt.AlignRight
                    text: `${Math.round(batteryTankRoot.batteryPercentage * 100)}%`
                    font.pointSize: Appearance.font.size.extraLarge
                    font.weight: Font.Medium
                    color: batteryTankRoot.batteryAccentColor
                }

                StyledText {
                    Layout.alignment: Qt.AlignRight
                    text: {
                        if (UPower.displayDevice.state === UPowerDeviceState.FullyCharged)
                            return "Full";

                        if (batteryTankRoot.isBatteryCharging)
                            return "Charging";

                        const remainingSeconds = UPower.displayDevice.timeToEmpty;
                        if (remainingSeconds === 0)
                            return "...";

                        const remainingHours = Math.floor(remainingSeconds / 3600);
                        const remainingMinutes = Math.floor((remainingSeconds % 3600) / 60);
                        if (remainingHours > 0)
                            return `${remainingHours}h ${remainingMinutes}m`;

                        return `${remainingMinutes}m`;
                    }
                    font.pointSize: Appearance.font.size.smaller
                    color: Colours.palette.m3onSurfaceVariant
                }
            }
        }

        Behavior on animatedBatteryPercentage {
            Anim {
                duration: Appearance.anim.durations.large
            }
        }
    }
}
