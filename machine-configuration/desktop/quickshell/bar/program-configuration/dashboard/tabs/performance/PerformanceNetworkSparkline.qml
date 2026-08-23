pragma ComponentBehavior: Bound

import "../../components"
import "../../services"
import "../.."
import QtQuick

Canvas {
    id: networkSparklineRoot

    property bool dashboardIsActive: false
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
            networkSparklineRoot.requestPaint();
        }

        target: Colours
    }

    Timer {
        interval: DashboardConfig.resourceUpdateInterval
        running: networkSparklineRoot.dashboardIsActive
        repeat: true
        onTriggered: networkSparklineRoot.internalTickCount++
    }

    NumberAnimation on slideAnimationProgress {
        from: 0
        to: 1
        duration: DashboardConfig.resourceUpdateInterval
        loops: Animation.Infinite
        running: networkSparklineRoot.dashboardIsActive
    }

    Behavior on smoothedMaximum {
        Anim {
            duration: Appearance.anim.durations.large
        }
    }
}
