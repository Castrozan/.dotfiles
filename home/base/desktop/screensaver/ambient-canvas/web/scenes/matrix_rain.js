(function registerMatrixRainScene() {
  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};

  const katakanaGlyphRangeStart = 0x30a0;
  const katakanaGlyphRangeEnd = 0x30ff;
  const supplementalGlyphCharacters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const defaultBackgroundColorChannels = "14, 30, 51";
  const trailFadeOpacity = 0.1;
  const leadingGlyphFillStyle = "#c8ffd0";
  const trailingGlyphColorChannels = "47, 191, 95";
  const minimumFallSpeedRowsPerSecond = 8;
  const maximumFallSpeedRowsPerSecond = 20;
  const glyphRerollProbabilityPerFrame = 0.02;
  const baseFontSizeInLogicalPixels = 16;
  const trailRowCount = 20;

  function pickRandomGlyphCharacter() {
    if (Math.random() < 0.6) {
      const katakanaCodePointCount =
        katakanaGlyphRangeEnd - katakanaGlyphRangeStart + 1;
      const katakanaCodePoint =
        katakanaGlyphRangeStart +
        Math.floor(Math.random() * katakanaCodePointCount);
      return String.fromCharCode(katakanaCodePoint);
    }
    const supplementalGlyphIndex = Math.floor(
      Math.random() * supplementalGlyphCharacters.length,
    );
    return supplementalGlyphCharacters.charAt(supplementalGlyphIndex);
  }

  function randomFallSpeedRowsPerSecond() {
    const fallSpeedRange =
      maximumFallSpeedRowsPerSecond - minimumFallSpeedRowsPerSecond;
    return minimumFallSpeedRowsPerSecond + Math.random() * fallSpeedRange;
  }

  function createMatrixRainRenderer(canvasElement, options) {
    const drawingContext = canvasElement.getContext("2d");
    const devicePixelRatio = options.devicePixelRatio || 1;
    const trailFadeFillStyle = `rgba(${
      options.backgroundColorChannels || defaultBackgroundColorChannels
    }, ${trailFadeOpacity})`;
    const fontSizeInDevicePixels = Math.round(
      baseFontSizeInLogicalPixels * devicePixelRatio,
    );

    let previousElapsedSeconds = 0;
    let columnCount = 0;
    let visibleRowCount = 0;
    let columnHeadRows = [];
    let columnFallSpeeds = [];
    let columnGlyphGrids = [];

    function randomNegativeStartRow() {
      return -Math.floor(Math.random() * visibleRowCount) - 1;
    }

    function buildGlyphGridForColumn() {
      const glyphGrid = new Array(visibleRowCount);
      for (let rowIndex = 0; rowIndex < visibleRowCount; rowIndex += 1) {
        glyphGrid[rowIndex] = pickRandomGlyphCharacter();
      }
      return glyphGrid;
    }

    function resize(pixelWidthDevice, pixelHeightDevice) {
      columnCount = Math.floor(pixelWidthDevice / fontSizeInDevicePixels) || 1;
      visibleRowCount =
        Math.ceil(pixelHeightDevice / fontSizeInDevicePixels) || 1;
      columnHeadRows = new Array(columnCount);
      columnFallSpeeds = new Array(columnCount);
      columnGlyphGrids = new Array(columnCount);
      for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
        columnHeadRows[columnIndex] = randomNegativeStartRow();
        columnFallSpeeds[columnIndex] = randomFallSpeedRowsPerSecond();
        columnGlyphGrids[columnIndex] = buildGlyphGridForColumn();
      }
      drawingContext.font = fontSizeInDevicePixels + "px monospace";
      drawingContext.textBaseline = "top";
    }

    function trailingGlyphFillStyleForDepth(trailDepth) {
      const fadeAmount = Math.max(0, 1 - trailDepth / trailRowCount);
      return `rgba(${trailingGlyphColorChannels}, ${fadeAmount.toFixed(3)})`;
    }

    function drawColumn(columnIndex) {
      const headRow = Math.floor(columnHeadRows[columnIndex]);
      const horizontalPixel = columnIndex * fontSizeInDevicePixels;
      const glyphGrid = columnGlyphGrids[columnIndex];
      for (let trailDepth = 0; trailDepth < trailRowCount; trailDepth += 1) {
        const rowIndex = headRow - trailDepth;
        if (rowIndex < 0 || rowIndex >= visibleRowCount) {
          continue;
        }
        if (Math.random() < glyphRerollProbabilityPerFrame) {
          glyphGrid[rowIndex] = pickRandomGlyphCharacter();
        }
        drawingContext.fillStyle =
          trailDepth === 0
            ? leadingGlyphFillStyle
            : trailingGlyphFillStyleForDepth(trailDepth);
        drawingContext.fillText(
          glyphGrid[rowIndex],
          horizontalPixel,
          rowIndex * fontSizeInDevicePixels,
        );
      }
    }

    function advanceColumn(columnIndex, deltaSeconds) {
      columnHeadRows[columnIndex] +=
        deltaSeconds * columnFallSpeeds[columnIndex];
      if (columnHeadRows[columnIndex] > visibleRowCount + trailRowCount) {
        columnHeadRows[columnIndex] = randomNegativeStartRow();
        columnFallSpeeds[columnIndex] = randomFallSpeedRowsPerSecond();
      }
    }

    function render(elapsedSeconds) {
      const rawDeltaSeconds = elapsedSeconds - previousElapsedSeconds;
      const deltaSeconds = Math.min(0.1, Math.max(0, rawDeltaSeconds));
      previousElapsedSeconds = elapsedSeconds;
      drawingContext.fillStyle = trailFadeFillStyle;
      drawingContext.fillRect(0, 0, canvasElement.width, canvasElement.height);
      for (let columnIndex = 0; columnIndex < columnCount; columnIndex += 1) {
        drawColumn(columnIndex);
        advanceColumn(columnIndex, deltaSeconds);
      }
    }

    resize(canvasElement.width, canvasElement.height);
    return { render, resize };
  }

  window.AMBIENT_CANVAS_SCENE_FACTORIES["matrix"] = createMatrixRainRenderer;
})();
