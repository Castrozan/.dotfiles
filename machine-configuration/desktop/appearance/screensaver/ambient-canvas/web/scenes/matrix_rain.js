const matrixRainKatakanaGlyphRangeStart = 0x30a0;
const matrixRainKatakanaGlyphRangeEnd = 0x30ff;
const matrixRainSupplementalGlyphCharacters =
  "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const matrixRainDefaultBackgroundColorChannels =
  window.AmbientCanvasPalette.backgroundColorChannels;
const matrixRainTrailFadeOpacity = 0.1;
const matrixRainLeadingGlyphFillStyle = "#c8ffd0";
const matrixRainTrailingGlyphColorChannels = "47, 191, 95";
const matrixRainMinimumFallSpeedRowsPerSecond = 8;
const matrixRainMaximumFallSpeedRowsPerSecond = 20;
const matrixRainGlyphRerollProbabilityPerFrame = 0.02;
const matrixRainBaseFontSizeInLogicalPixels = 16;
const matrixRainTrailRowCount = 20;

function matrixRainPickRandomGlyphCharacter() {
  if (Math.random() < 0.6) {
    const katakanaCodePointCount =
      matrixRainKatakanaGlyphRangeEnd - matrixRainKatakanaGlyphRangeStart + 1;
    const katakanaCodePoint =
      matrixRainKatakanaGlyphRangeStart +
      Math.floor(Math.random() * katakanaCodePointCount);
    return String.fromCharCode(katakanaCodePoint);
  }
  const supplementalGlyphIndex = Math.floor(
    Math.random() * matrixRainSupplementalGlyphCharacters.length,
  );
  return matrixRainSupplementalGlyphCharacters.charAt(supplementalGlyphIndex);
}

function matrixRainRandomFallSpeedRowsPerSecond() {
  const fallSpeedRange =
    matrixRainMaximumFallSpeedRowsPerSecond -
    matrixRainMinimumFallSpeedRowsPerSecond;
  return (
    matrixRainMinimumFallSpeedRowsPerSecond + Math.random() * fallSpeedRange
  );
}

function matrixRainRandomNegativeStartRow(state) {
  return -Math.floor(Math.random() * state.visibleRowCount) - 1;
}

function matrixRainBuildGlyphGridForColumn(state) {
  const glyphGrid = new Array(state.visibleRowCount);
  for (let rowIndex = 0; rowIndex < state.visibleRowCount; rowIndex += 1) {
    glyphGrid[rowIndex] = matrixRainPickRandomGlyphCharacter();
  }
  return glyphGrid;
}

function matrixRainResizeGrid(state, pixelWidthDevice, pixelHeightDevice) {
  state.columnCount =
    Math.floor(pixelWidthDevice / state.fontSizeInDevicePixels) || 1;
  state.visibleRowCount =
    Math.ceil(pixelHeightDevice / state.fontSizeInDevicePixels) || 1;
  state.columnHeadRows = new Array(state.columnCount);
  state.columnFallSpeeds = new Array(state.columnCount);
  state.columnGlyphGrids = new Array(state.columnCount);
  for (let columnIndex = 0; columnIndex < state.columnCount; columnIndex += 1) {
    state.columnHeadRows[columnIndex] = matrixRainRandomNegativeStartRow(state);
    state.columnFallSpeeds[columnIndex] =
      matrixRainRandomFallSpeedRowsPerSecond();
    state.columnGlyphGrids[columnIndex] =
      matrixRainBuildGlyphGridForColumn(state);
  }
  state.drawingContext.font = `${state.fontSizeInDevicePixels}px monospace`;
  state.drawingContext.textBaseline = "top";
  state.drawingContext.fillStyle = window.AmbientCanvasPalette.backgroundHex;
  state.drawingContext.fillRect(0, 0, pixelWidthDevice, pixelHeightDevice);
}

function matrixRainTrailingGlyphFillStyleForDepth(trailDepth) {
  const fadeAmount = Math.max(0, 1 - trailDepth / matrixRainTrailRowCount);
  return `rgba(${matrixRainTrailingGlyphColorChannels}, ${fadeAmount.toFixed(3)})`;
}

function matrixRainDrawColumn(state, columnIndex) {
  const headRow = Math.floor(state.columnHeadRows[columnIndex]);
  const horizontalPixel = columnIndex * state.fontSizeInDevicePixels;
  const glyphGrid = state.columnGlyphGrids[columnIndex];
  for (
    let trailDepth = 0;
    trailDepth < matrixRainTrailRowCount;
    trailDepth += 1
  ) {
    const rowIndex = headRow - trailDepth;
    matrixRainDrawColumnGlyphRow(
      state,
      glyphGrid,
      rowIndex,
      trailDepth,
      horizontalPixel,
    );
  }
}

function matrixRainDrawColumnGlyphRow(
  state,
  glyphGrid,
  rowIndex,
  trailDepth,
  horizontalPixel,
) {
  if (rowIndex < 0 || rowIndex >= state.visibleRowCount) return;
  if (Math.random() < matrixRainGlyphRerollProbabilityPerFrame) {
    glyphGrid[rowIndex] = matrixRainPickRandomGlyphCharacter();
  }
  state.drawingContext.fillStyle =
    trailDepth === 0
      ? matrixRainLeadingGlyphFillStyle
      : matrixRainTrailingGlyphFillStyleForDepth(trailDepth);
  state.drawingContext.fillText(
    glyphGrid[rowIndex],
    horizontalPixel,
    rowIndex * state.fontSizeInDevicePixels,
  );
}

function matrixRainAdvanceColumn(state, columnIndex, deltaSeconds) {
  state.columnHeadRows[columnIndex] =
    state.columnHeadRows[columnIndex] +
    deltaSeconds * state.columnFallSpeeds[columnIndex];
  if (
    state.columnHeadRows[columnIndex] >
    state.visibleRowCount + matrixRainTrailRowCount
  ) {
    state.columnHeadRows[columnIndex] = matrixRainRandomNegativeStartRow(state);
    state.columnFallSpeeds[columnIndex] =
      matrixRainRandomFallSpeedRowsPerSecond();
  }
}

function matrixRainRenderFrame(state, elapsedSeconds) {
  const rawDeltaSeconds = elapsedSeconds - state.previousElapsedSeconds;
  const deltaSeconds = Math.min(0.1, Math.max(0, rawDeltaSeconds));
  state.previousElapsedSeconds = elapsedSeconds;
  state.drawingContext.fillStyle = state.trailFadeFillStyle;
  state.drawingContext.fillRect(
    0,
    0,
    state.canvasElement.width,
    state.canvasElement.height,
  );
  for (let columnIndex = 0; columnIndex < state.columnCount; columnIndex += 1) {
    matrixRainDrawColumn(state, columnIndex);
    matrixRainAdvanceColumn(state, columnIndex, deltaSeconds);
  }
}

(function registerMatrixRainScene() {
  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  function createMatrixRainRenderer(canvasElement, options) {
    const devicePixelRatio = options.devicePixelRatio || 1;
    const state = {
      canvasElement,
      drawingContext: canvasElement.getContext("2d"),
      trailFadeFillStyle: `rgba(${
        options.backgroundColorChannels ||
        matrixRainDefaultBackgroundColorChannels
      }, ${matrixRainTrailFadeOpacity})`,
      fontSizeInDevicePixels: Math.round(
        matrixRainBaseFontSizeInLogicalPixels * devicePixelRatio,
      ),
      previousElapsedSeconds: 0,
      columnCount: 0,
      visibleRowCount: 0,
      columnHeadRows: [],
      columnFallSpeeds: [],
      columnGlyphGrids: [],
    };
    matrixRainResizeGrid(state, canvasElement.width, canvasElement.height);
    return {
      render: (elapsedSeconds) => matrixRainRenderFrame(state, elapsedSeconds),
      resize: (pixelWidthDevice, pixelHeightDevice) =>
        matrixRainResizeGrid(state, pixelWidthDevice, pixelHeightDevice),
    };
  }

  window.AMBIENT_CANVAS_SCENE_FACTORIES["matrix"] = createMatrixRainRenderer;
})();
