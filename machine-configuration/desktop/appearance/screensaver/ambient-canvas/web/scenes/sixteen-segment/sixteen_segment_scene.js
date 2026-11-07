const SIXTEEN_SEGMENT_HALF_WIDTH_IN_CELL_HEIGHTS = 0.042;
const SIXTEEN_SEGMENT_END_GAP_IN_CELL_HEIGHTS = 0.03;
const SIXTEEN_SEGMENT_BLOOM_HALF_WIDTH_MULTIPLIER = 2.6;
const SIXTEEN_SEGMENT_BLOOM_ALPHA_SCALE = 0.13;

const sixteenSegmentGeometry = window.AmbientCanvasSixteenSegmentGeometry;
const sixteenSegmentField = window.AmbientCanvasSixteenSegmentField;
const sixteenSegmentLayout = window.AmbientCanvasSixteenSegmentLayout;

function sixteenSegmentResolveMonochromeFillStyle(joinedColorChannels, alpha) {
  const colorChannels = joinedColorChannels.split(",").map(Number);
  const monochromeChannel = sixteenSegmentField.resolveMonochromeChannel(
    colorChannels[0],
    colorChannels[1],
    colorChannels[2],
  );
  return `rgba(${monochromeChannel}, ${monochromeChannel}, ${monochromeChannel}, ${alpha})`;
}

const SIXTEEN_SEGMENT_UNLIT_SEGMENT_FILL_STYLE = sixteenSegmentResolveMonochromeFillStyle(
  window.AmbientCanvasPalette.accentOrangeColorChannels,
  0.062,
);
const SIXTEEN_SEGMENT_BACKGROUND_FILL_STYLE = window.AmbientCanvasPalette.backgroundHex;

function sixteenSegmentFillSegmentPolygon(drawingContext, polygon, fillStyle) {
  drawingContext.fillStyle = fillStyle;
  drawingContext.beginPath();
  drawingContext.moveTo(polygon[0], polygon[1]);
  for (let corner = 2; corner < polygon.length; corner += 2) {
    drawingContext.lineTo(polygon[corner], polygon[corner + 1]);
  }
  drawingContext.closePath();
  drawingContext.fill();
}

function sixteenSegmentBuildSegmentPolygons(
  cellPixelWidth,
  cellPixelHeight,
  halfWidthMultiplier,
) {
  const halfWidthPixels =
    cellPixelHeight * SIXTEEN_SEGMENT_HALF_WIDTH_IN_CELL_HEIGHTS * halfWidthMultiplier;
  const endGapPixels = cellPixelHeight * SIXTEEN_SEGMENT_END_GAP_IN_CELL_HEIGHTS;
  return sixteenSegmentGeometry.segmentAxes.map((segmentAxis) =>
    sixteenSegmentGeometry.buildSegmentPolygon(
      segmentAxis,
      cellPixelWidth,
      cellPixelHeight,
      halfWidthPixels,
      endGapPixels,
    ),
  );
}

function sixteenSegmentPaintEveryCell(renderState, targetContext, paintCell) {
  const wallLayout = renderState.wallLayout;
  for (
    let cellIndex = 0;
    cellIndex < sixteenSegmentLayout.displayCount;
    cellIndex += 1
  ) {
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

function sixteenSegmentBuildUnlitLayer(renderState, pixelWidthDevice, pixelHeightDevice) {
  const unlitLayerCanvas = document.createElement("canvas");
  unlitLayerCanvas.width = pixelWidthDevice;
  unlitLayerCanvas.height = pixelHeightDevice;
  renderState.unlitLayerCanvas = unlitLayerCanvas;
  const unlitContext = unlitLayerCanvas.getContext("2d");
  sixteenSegmentPaintEveryCell(renderState, unlitContext, () =>
    renderState.corePolygons.forEach((corePolygon) => {
      sixteenSegmentFillSegmentPolygon(unlitContext, corePolygon, SIXTEEN_SEGMENT_UNLIT_SEGMENT_FILL_STYLE);
    }),
  );
}

function sixteenSegmentResizeWall(
  renderState,
  pixelWidthDevice,
  pixelHeightDevice,
) {
  const wallLayout = sixteenSegmentLayout.resolveDisplayWallLayout(
    pixelWidthDevice,
    pixelHeightDevice,
  );
  renderState.wallLayout = wallLayout;
  const { cellPixelWidth, cellPixelHeight } = wallLayout;
  renderState.corePolygons = sixteenSegmentBuildSegmentPolygons(
    cellPixelWidth,
    cellPixelHeight,
    1,
  );
  renderState.bloomPolygons = sixteenSegmentBuildSegmentPolygons(
    cellPixelWidth,
    cellPixelHeight,
    SIXTEEN_SEGMENT_BLOOM_HALF_WIDTH_MULTIPLIER,
  );
  renderState.segmentAngles = sixteenSegmentGeometry.segmentAxes.map(
    (segmentAxis) =>
      sixteenSegmentGeometry.measureSegmentAngle(
        segmentAxis,
        cellPixelWidth,
        cellPixelHeight,
      ),
  );
  sixteenSegmentBuildUnlitLayer(renderState, pixelWidthDevice, pixelHeightDevice);
}

function sixteenSegmentPaintLitSegments(renderState, cellIndex, elapsedSeconds, displayGain) {
  const wallLayout = renderState.wallLayout;
  for (
    let segment = 0;
    segment < sixteenSegmentLayout.segmentCount;
    segment += 1
  ) {
    const fieldOffset = cellIndex * sixteenSegmentLayout.segmentCount + segment;
    const intensity = sixteenSegmentField.resolveSegmentIntensity(
      wallLayout.segmentFieldXs[fieldOffset],
      wallLayout.segmentFieldYs[fieldOffset],
      renderState.segmentAngles[segment],
      elapsedSeconds,
      displayGain,
    );
    if (intensity <= 0) {
      continue;
    }
    const intensityLevel = sixteenSegmentField.resolveIntensityLevel(intensity);
    sixteenSegmentFillSegmentPolygon(
      renderState.drawingContext,
      renderState.bloomPolygons[segment],
      renderState.bloomFillStyles[intensityLevel],
    );
    sixteenSegmentFillSegmentPolygon(
      renderState.drawingContext,
      renderState.corePolygons[segment],
      renderState.coreFillStyles[intensityLevel],
    );
  }
}

function sixteenSegmentRenderFrame(renderState, elapsedSeconds) {
  const displayGain = sixteenSegmentField.resolveDisplayGain(elapsedSeconds);
  const { canvasElement, drawingContext, unlitLayerCanvas } = renderState;
  drawingContext.setTransform(1, 0, 0, 1, 0, 0);
  drawingContext.globalCompositeOperation = "source-over";
  drawingContext.fillStyle = SIXTEEN_SEGMENT_BACKGROUND_FILL_STYLE;
  drawingContext.fillRect(0, 0, canvasElement.width, canvasElement.height);
  drawingContext.drawImage(unlitLayerCanvas, 0, 0);
  drawingContext.globalCompositeOperation = "lighter";
  sixteenSegmentPaintEveryCell(renderState, drawingContext, (cellIndex) =>
    sixteenSegmentPaintLitSegments(renderState, cellIndex, elapsedSeconds, displayGain),
  );
  drawingContext.globalCompositeOperation = "source-over";
}

function sixteenSegmentCreateRenderer(canvasElement) {
  const renderState = {
    canvasElement,
    drawingContext: canvasElement.getContext("2d"),
    coreFillStyles: sixteenSegmentField.buildLitFillStyles(1),
    bloomFillStyles: sixteenSegmentField.buildLitFillStyles(SIXTEEN_SEGMENT_BLOOM_ALPHA_SCALE),
    wallLayout: null,
    corePolygons: [],
    bloomPolygons: [],
    segmentAngles: [],
    unlitLayerCanvas: null,
  };
  sixteenSegmentResizeWall(
    renderState,
    canvasElement.width,
    canvasElement.height,
  );
  return {
    render: sixteenSegmentRenderFrame.bind(null, renderState),
    resize: sixteenSegmentResizeWall.bind(null, renderState),
  };
}

(function registerSixteenSegmentScene() {
  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  window.AMBIENT_CANVAS_SCENE_FACTORIES["sixteen-segment"] =
    sixteenSegmentCreateRenderer;
})();
