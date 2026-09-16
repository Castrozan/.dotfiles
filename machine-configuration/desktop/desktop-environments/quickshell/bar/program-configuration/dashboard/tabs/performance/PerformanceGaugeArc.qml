pragma ComponentBehavior: Bound

import "../.."
import QtQuick

Canvas {
    id: performanceGaugeArcRoot

    property real percentage: 0
    property color accentColor: Colours.palette.m3primary
    readonly property real arcStartAngle: 0.75 * Math.PI
    readonly property real arcSweepAngle: 1.5 * Math.PI
    readonly property real arcDiameterInset: 12
    readonly property real arcLineWidth: 10

    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        const centerX = width / 2;
        const centerY = height / 2;
        const arcRadius = (Math.min(width, height) - arcDiameterInset) / 2;
        ctx.beginPath();
        ctx.arc(centerX, centerY, arcRadius, arcStartAngle, arcStartAngle + arcSweepAngle);
        ctx.lineWidth = arcLineWidth;
        ctx.lineCap = "round";
        ctx.strokeStyle = Colours.layer(Colours.palette.m3surfaceContainerHigh, 2);
        ctx.stroke();
        if (percentage > 0) {
            ctx.beginPath();
            ctx.arc(centerX, centerY, arcRadius, arcStartAngle, arcStartAngle + arcSweepAngle * percentage);
            ctx.lineWidth = arcLineWidth;
            ctx.lineCap = "round";
            ctx.strokeStyle = accentColor;
            ctx.stroke();
        }
    }
    onPercentageChanged: requestPaint()
    Component.onCompleted: requestPaint()

    Connections {
        function onPaletteChanged() {
            performanceGaugeArcRoot.requestPaint();
        }

        target: Colours
    }
}
