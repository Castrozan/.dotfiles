window.AmbientCanvasBrailleGlyphGrid = (function buildBrailleGlyphGrid() {
  const BRAILLE_DOT_COLUMNS_PER_CELL = 2;
  const BRAILLE_DOT_ROWS_PER_CELL = 4;
  const FULLY_RAISED_BRAILLE_CELL = "⣿";

  function resolveGlyphGrid(
    displayContext,
    canvasElement,
    characterRows,
    glyphFontFamily,
  ) {
    const fontSize = canvasElement.height / characterRows;
    displayContext.font = fontSize + "px " + glyphFontFamily;
    const advanceWidth =
      displayContext.measureText(FULLY_RAISED_BRAILLE_CELL).width || fontSize;
    const characterColumns = Math.max(
      1,
      Math.floor(canvasElement.width / advanceWidth),
    );
    return {
      fontSize: fontSize,
      advanceWidth: advanceWidth,
      characterRows: characterRows,
      characterColumns: characterColumns,
      dotColumns: characterColumns * BRAILLE_DOT_COLUMNS_PER_CELL,
      dotRows: characterRows * BRAILLE_DOT_ROWS_PER_CELL,
      dotPixelWidth: advanceWidth / BRAILLE_DOT_COLUMNS_PER_CELL,
      dotPixelHeight: fontSize / BRAILLE_DOT_ROWS_PER_CELL,
    };
  }

  function drawSourceIntoDotGrid(
    samplingContext,
    imageSource,
    sourcePixelWidth,
    sourcePixelHeight,
    glyphGrid,
  ) {
    samplingContext.fillStyle = "#000000";
    samplingContext.fillRect(0, 0, glyphGrid.dotColumns, glyphGrid.dotRows);
    const fittedScale = Math.min(
      (glyphGrid.dotColumns * glyphGrid.dotPixelWidth) / sourcePixelWidth,
      (glyphGrid.dotRows * glyphGrid.dotPixelHeight) / sourcePixelHeight,
    );
    const drawnDotWidth =
      (sourcePixelWidth * fittedScale) / glyphGrid.dotPixelWidth;
    const drawnDotHeight =
      (sourcePixelHeight * fittedScale) / glyphGrid.dotPixelHeight;
    samplingContext.drawImage(
      imageSource,
      (glyphGrid.dotColumns - drawnDotWidth) / 2,
      (glyphGrid.dotRows - drawnDotHeight) / 2,
      drawnDotWidth,
      drawnDotHeight,
    );
  }

  return {
    dotColumnsPerCell: BRAILLE_DOT_COLUMNS_PER_CELL,
    dotRowsPerCell: BRAILLE_DOT_ROWS_PER_CELL,
    resolveGlyphGrid: resolveGlyphGrid,
    drawSourceIntoDotGrid: drawSourceIntoDotGrid,
  };
})();
