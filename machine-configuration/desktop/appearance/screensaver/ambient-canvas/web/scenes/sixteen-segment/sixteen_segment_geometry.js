window.AmbientCanvasSixteenSegmentGeometry =
  (function buildSixteenSegmentGeometry() {
    const DIAGONAL_WIDTH_SCALE = 0.6;

    const SEGMENT_AXES = [
      { startX: 0.0, startY: 0.0, endX: 0.5, endY: 0.0, widthScale: 1.0 },
      { startX: 0.5, startY: 0.0, endX: 1.0, endY: 0.0, widthScale: 1.0 },
      { startX: 1.0, startY: 0.0, endX: 1.0, endY: 0.5, widthScale: 1.0 },
      { startX: 1.0, startY: 0.5, endX: 1.0, endY: 1.0, widthScale: 1.0 },
      { startX: 1.0, startY: 1.0, endX: 0.5, endY: 1.0, widthScale: 1.0 },
      { startX: 0.5, startY: 1.0, endX: 0.0, endY: 1.0, widthScale: 1.0 },
      { startX: 0.0, startY: 1.0, endX: 0.0, endY: 0.5, widthScale: 1.0 },
      { startX: 0.0, startY: 0.5, endX: 0.0, endY: 0.0, widthScale: 1.0 },
      { startX: 0.0, startY: 0.5, endX: 0.5, endY: 0.5, widthScale: 1.0 },
      { startX: 0.5, startY: 0.5, endX: 1.0, endY: 0.5, widthScale: 1.0 },
      {
        startX: 0.0,
        startY: 0.0,
        endX: 0.5,
        endY: 0.5,
        widthScale: DIAGONAL_WIDTH_SCALE,
      },
      { startX: 0.5, startY: 0.0, endX: 0.5, endY: 0.5, widthScale: 1.0 },
      {
        startX: 1.0,
        startY: 0.0,
        endX: 0.5,
        endY: 0.5,
        widthScale: DIAGONAL_WIDTH_SCALE,
      },
      {
        startX: 0.0,
        startY: 1.0,
        endX: 0.5,
        endY: 0.5,
        widthScale: DIAGONAL_WIDTH_SCALE,
      },
      { startX: 0.5, startY: 1.0, endX: 0.5, endY: 0.5, widthScale: 1.0 },
      {
        startX: 1.0,
        startY: 1.0,
        endX: 0.5,
        endY: 0.5,
        widthScale: DIAGONAL_WIDTH_SCALE,
      },
    ];

    function buildSegmentPolygon(
      segmentAxis,
      cellPixelWidth,
      cellPixelHeight,
      halfWidthPixels,
      endGapPixels,
    ) {
      const startPixelX = segmentAxis.startX * cellPixelWidth;
      const startPixelY = segmentAxis.startY * cellPixelHeight;
      const endPixelX = segmentAxis.endX * cellPixelWidth;
      const endPixelY = segmentAxis.endY * cellPixelHeight;
      const axisLength = Math.hypot(
        endPixelX - startPixelX,
        endPixelY - startPixelY,
      );
      const directionX = (endPixelX - startPixelX) / axisLength;
      const directionY = (endPixelY - startPixelY) / axisLength;
      const normalX = -directionY;
      const normalY = directionX;
      const halfWidth = halfWidthPixels * segmentAxis.widthScale;
      const trimmedGap = Math.min(endGapPixels, axisLength / 2 - halfWidth);
      const insetStartX = startPixelX + directionX * trimmedGap;
      const insetStartY = startPixelY + directionY * trimmedGap;
      const insetEndX = endPixelX - directionX * trimmedGap;
      const insetEndY = endPixelY - directionY * trimmedGap;
      return [
        insetStartX + normalX * halfWidth,
        insetStartY + normalY * halfWidth,
        insetEndX + normalX * halfWidth,
        insetEndY + normalY * halfWidth,
        insetEndX + directionX * halfWidth,
        insetEndY + directionY * halfWidth,
        insetEndX - normalX * halfWidth,
        insetEndY - normalY * halfWidth,
        insetStartX - normalX * halfWidth,
        insetStartY - normalY * halfWidth,
        insetStartX - directionX * halfWidth,
        insetStartY - directionY * halfWidth,
      ];
    }

    function measureSegmentAngle(segmentAxis, cellPixelWidth, cellPixelHeight) {
      return Math.atan2(
        (segmentAxis.endY - segmentAxis.startY) * cellPixelHeight,
        (segmentAxis.endX - segmentAxis.startX) * cellPixelWidth,
      );
    }

    function measureSegmentCenterX(segmentAxis) {
      return (segmentAxis.startX + segmentAxis.endX) / 2;
    }

    function measureSegmentCenterY(segmentAxis) {
      return (segmentAxis.startY + segmentAxis.endY) / 2;
    }

    return {
      segmentAxes: SEGMENT_AXES,
      buildSegmentPolygon,
      measureSegmentAngle,
      measureSegmentCenterX,
      measureSegmentCenterY,
    };
  })();
