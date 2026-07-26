(function registerSixteenSegmentScene() {
  const SEGMENT_HALF_WIDTH_IN_CELL_HEIGHTS = 0.042;
  const SEGMENT_END_GAP_IN_CELL_HEIGHTS = 0.03;
  const BLOOM_HALF_WIDTH_MULTIPLIER = 2.6;
  const BLOOM_ALPHA_SCALE = 0.13;
  const UNLIT_SEGMENT_FILL_STYLE = "rgba(255, 108, 24, 0.062)";
  const BACKGROUND_FILL_STYLE = "#05060a";

  const geometry = window.AmbientCanvasSixteenSegmentGeometry;
  const field = window.AmbientCanvasSixteenSegmentField;
  const layout = window.AmbientCanvasSixteenSegmentLayout;

  function fillSegmentPolygon(drawingContext, polygon, fillStyle) {
    drawingContext.fillStyle = fillStyle;
    drawingContext.beginPath();
    drawingContext.moveTo(polygon[0], polygon[1]);
    for (let corner = 2; corner < polygon.length; corner += 2) {
      drawingContext.lineTo(polygon[corner], polygon[corner + 1]);
    }
    drawingContext.closePath();
    drawingContext.fill();
  }

  function buildSegmentPolygons(
    cellPixelWidth,
    cellPixelHeight,
    halfWidthMultiplier,
  ) {
    const halfWidthPixels =
      cellPixelHeight *
      SEGMENT_HALF_WIDTH_IN_CELL_HEIGHTS *
      halfWidthMultiplier;
    const endGapPixels = cellPixelHeight * SEGMENT_END_GAP_IN_CELL_HEIGHTS;
    return geometry.segmentAxes.map((segmentAxis) =>
      geometry.buildSegmentPolygon(
        segmentAxis,
        cellPixelWidth,
        cellPixelHeight,
        halfWidthPixels,
        endGapPixels,
      ),
    );
  }

  function createSixteenSegmentRenderer(canvasElement) {
    const drawingContext = canvasElement.getContext("2d");
    const coreFillStyles = field.buildLitFillStyles(1);
    const bloomFillStyles = field.buildLitFillStyles(BLOOM_ALPHA_SCALE);

    let wallLayout = null;
    let corePolygons = [];
    let bloomPolygons = [];
    let segmentAngles = [];
    let unlitLayerCanvas = null;

    function paintEveryCell(targetContext, paintCell) {
      for (let cellIndex = 0; cellIndex < layout.displayCount; cellIndex += 1) {
        targetContext.setTransform(
          1,
          0,
          0,
          1,
          wallLayout.cellOriginXs[cellIndex],
          wallLayout.cellOriginYs[cellIndex],
        );
        paintCell(cellIndex);
      }
      targetContext.setTransform(1, 0, 0, 1, 0, 0);
    }

    function buildUnlitLayer(pixelWidthDevice, pixelHeightDevice) {
      unlitLayerCanvas = document.createElement("canvas");
      unlitLayerCanvas.width = pixelWidthDevice;
      unlitLayerCanvas.height = pixelHeightDevice;
      const unlitContext = unlitLayerCanvas.getContext("2d");
      paintEveryCell(unlitContext, () => {
        for (let segment = 0; segment < layout.segmentCount; segment += 1) {
          fillSegmentPolygon(
            unlitContext,
            corePolygons[segment],
            UNLIT_SEGMENT_FILL_STYLE,
          );
        }
      });
    }

    function resize(pixelWidthDevice, pixelHeightDevice) {
      wallLayout = layout.resolveDisplayWallLayout(
        pixelWidthDevice,
        pixelHeightDevice,
      );
      corePolygons = buildSegmentPolygons(
        wallLayout.cellPixelWidth,
        wallLayout.cellPixelHeight,
        1,
      );
      bloomPolygons = buildSegmentPolygons(
        wallLayout.cellPixelWidth,
        wallLayout.cellPixelHeight,
        BLOOM_HALF_WIDTH_MULTIPLIER,
      );
      segmentAngles = geometry.segmentAxes.map((segmentAxis) =>
        geometry.measureSegmentAngle(
          segmentAxis,
          wallLayout.cellPixelWidth,
          wallLayout.cellPixelHeight,
        ),
      );
      buildUnlitLayer(pixelWidthDevice, pixelHeightDevice);
    }

    function paintLitSegments(cellIndex, elapsedSeconds, displayGain) {
      for (let segment = 0; segment < layout.segmentCount; segment += 1) {
        const fieldOffset = cellIndex * layout.segmentCount + segment;
        const intensity = field.resolveSegmentIntensity(
          wallLayout.segmentFieldXs[fieldOffset],
          wallLayout.segmentFieldYs[fieldOffset],
          segmentAngles[segment],
          elapsedSeconds,
          displayGain,
        );
        if (intensity <= 0) {
          continue;
        }
        const intensityLevel = field.resolveIntensityLevel(intensity);
        fillSegmentPolygon(
          drawingContext,
          bloomPolygons[segment],
          bloomFillStyles[intensityLevel],
        );
        fillSegmentPolygon(
          drawingContext,
          corePolygons[segment],
          coreFillStyles[intensityLevel],
        );
      }
    }

    function render(elapsedSeconds) {
      const displayGain = field.resolveDisplayGain(elapsedSeconds);
      drawingContext.setTransform(1, 0, 0, 1, 0, 0);
      drawingContext.globalCompositeOperation = "source-over";
      drawingContext.fillStyle = BACKGROUND_FILL_STYLE;
      drawingContext.fillRect(0, 0, canvasElement.width, canvasElement.height);
      drawingContext.drawImage(unlitLayerCanvas, 0, 0);
      drawingContext.globalCompositeOperation = "lighter";
      paintEveryCell(drawingContext, (cellIndex) =>
        paintLitSegments(cellIndex, elapsedSeconds, displayGain),
      );
      drawingContext.globalCompositeOperation = "source-over";
    }

    resize(canvasElement.width, canvasElement.height);
    return { render, resize };
  }

  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  window.AMBIENT_CANVAS_SCENE_FACTORIES["sixteen-segment"] =
    createSixteenSegmentRenderer;
})();
