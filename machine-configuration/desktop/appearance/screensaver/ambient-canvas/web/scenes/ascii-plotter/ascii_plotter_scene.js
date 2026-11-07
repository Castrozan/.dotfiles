const TARGET_VISIBLE_ROWS = 74;
const CELL_HEIGHT_TO_FONT_RATIO = 0.78;
const CELL_WIDTH_TO_FONT_RATIO = 0.6;
const ROWS_EMITTED_PER_SECOND = 6;
const PRE_ROLL_ROWS = 512;
const EMISSION_GLOW_ROWS = 9;
const SETTLED_FADE_ROWS = 17;
const RESIDUAL_STRUCTURE_ALPHA = 0.11;
const SETTLED_STRUCTURE_ALPHA = 0.34;
const EMISSION_STRUCTURE_ALPHA = 0.86;
const RESIDUAL_LATTICE_ALPHA = 0.17;
const EMISSION_LATTICE_ALPHA = 0.45;

function whiteAtAlpha(alpha) {
  return `rgba(255, 255, 255, ${Math.min(1, alpha).toFixed(3)})`;
}

function resizeAsciiPlotterRenderState(
  renderState,
  pixelWidthDevice,
  pixelHeightDevice,
) {
  renderState.cellHeightPixels = Math.max(
    6,
    pixelHeightDevice / TARGET_VISIBLE_ROWS,
  );
  const fontSizePixels = Math.round(
    renderState.cellHeightPixels / CELL_HEIGHT_TO_FONT_RATIO,
  );
  renderState.cellWidthPixels = fontSizePixels * CELL_WIDTH_TO_FONT_RATIO;
  renderState.columnCount =
    Math.floor(pixelWidthDevice / renderState.cellWidthPixels) || 1;
  renderState.visibleRowCount =
    Math.ceil(pixelHeightDevice / renderState.cellHeightPixels) + 1;
  renderState.drawingContext.font = `${fontSizePixels}px monospace`;
  renderState.drawingContext.textBaseline = "top";
}

function paintLatticeRow(renderState, sourceRow, verticalPixel, alpha) {
  const { drawingContext, schematic } = renderState;
  drawingContext.fillStyle = whiteAtAlpha(alpha);
  for (let column = 0; column < renderState.columnCount; column += 1) {
    const glyph = schematic.latticeGlyph(column, sourceRow);
    if (glyph) {
      drawingContext.fillText(
        glyph,
        column * renderState.cellWidthPixels,
        verticalPixel,
      );
    }
  }
}

function paintStructureRow(renderState, sourceRow, verticalPixel, alpha) {
  const { drawingContext, schematic } = renderState;
  const marks = schematic.buildRowMarks(sourceRow, renderState.columnCount);
  for (let index = 0; index < marks.length; index += 1) {
    const mark = marks[index];
    drawingContext.fillStyle = whiteAtAlpha(alpha * mark.weight);
    drawingContext.fillText(
      mark.glyph,
      mark.column * renderState.cellWidthPixels,
      verticalPixel,
    );
  }
}

function renderAsciiPlotterFrame(renderState, elapsedSeconds) {
  const { drawingContext, canvasElement } = renderState;
  drawingContext.fillStyle = window.AmbientCanvasPalette.backgroundHex;
  drawingContext.fillRect(0, 0, canvasElement.width, canvasElement.height);

  const emittedRows = PRE_ROLL_ROWS + elapsedSeconds * ROWS_EMITTED_PER_SECOND;
  const newestSourceRow = Math.floor(emittedRows);
  const subRowOffset = emittedRows - newestSourceRow;

  for (
    let screenRow = 0;
    screenRow < renderState.visibleRowCount;
    screenRow += 1
  ) {
    const sourceRow = newestSourceRow - screenRow;
    if (sourceRow < 0) {
      continue;
    }
    const verticalPixel =
      (screenRow + subRowOffset) * renderState.cellHeightPixels;
    const emissionGlow = Math.exp(-screenRow / EMISSION_GLOW_ROWS);
    const settled = Math.exp(-screenRow / SETTLED_FADE_ROWS);
    paintLatticeRow(
      renderState,
      sourceRow,
      verticalPixel,
      RESIDUAL_LATTICE_ALPHA + EMISSION_LATTICE_ALPHA * emissionGlow,
    );
    paintStructureRow(
      renderState,
      sourceRow,
      verticalPixel,
      RESIDUAL_STRUCTURE_ALPHA +
        SETTLED_STRUCTURE_ALPHA * settled +
        EMISSION_STRUCTURE_ALPHA * emissionGlow,
    );
  }
}

function createAsciiPlotterRenderer(canvasElement) {
  const renderState = {
    canvasElement,
    drawingContext: canvasElement.getContext("2d"),
    schematic: window.AmbientCanvasAsciiPlotterSchematic,
    cellHeightPixels: 1,
    cellWidthPixels: 1,
    columnCount: 1,
    visibleRowCount: 1,
  };
  resizeAsciiPlotterRenderState(
    renderState,
    canvasElement.width,
    canvasElement.height,
  );
  return {
    render: (elapsedSeconds) =>
      renderAsciiPlotterFrame(renderState, elapsedSeconds),
    resize: (pixelWidthDevice, pixelHeightDevice) =>
      resizeAsciiPlotterRenderState(
        renderState,
        pixelWidthDevice,
        pixelHeightDevice,
      ),
  };
}

(function registerAsciiPlotterScene() {
  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  window.AMBIENT_CANVAS_SCENE_FACTORIES["ascii-plotter"] =
    createAsciiPlotterRenderer;
})();
