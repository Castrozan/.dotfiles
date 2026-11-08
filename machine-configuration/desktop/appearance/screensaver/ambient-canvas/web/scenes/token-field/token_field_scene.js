(function registerTokenFieldScene() {
  const TARGET_VISIBLE_ROWS = 44;
  const SMALLEST_ROW_HEIGHT_PIXELS = 10;
  const FONT_SIZE_TO_ROW_HEIGHT = 0.76;
  const NOISE_ALPHA = 0.6;
  const INVISIBLE_ALPHA = 0.004;

  const timeline = window.AmbientCanvasTokenFieldTimeline;
  const vocabulary = window.AmbientCanvasTokenFieldVocabulary;
  const layoutModule = window.AmbientCanvasTokenFieldLayout;
  const glyphAtlas = window.AmbientCanvasTokenFieldGlyphAtlas;
  const palette = window.AmbientCanvasPalette;

  function rebuildGrid(state, pixelWidth, pixelHeight) {
    const rowHeight = Math.max(
      SMALLEST_ROW_HEIGHT_PIXELS,
      Math.floor(pixelHeight / TARGET_VISIBLE_ROWS),
    );
    const fontSize = Math.round(rowHeight * FONT_SIZE_TO_ROW_HEIGHT);
    state.cell = glyphAtlas.measureGlyphCell(fontSize, rowHeight);
    state.grid = {
      columnCount: Math.ceil(pixelWidth / state.cell.width),
      rowCount: Math.ceil(pixelHeight / state.cell.height),
    };
    state.layout = layoutModule.buildTokenFieldLayout(
      state.grid,
      timeline.GENERATION_COUNT,
      vocabulary,
    );
    state.atlas = glyphAtlas.buildGlyphAtlas(
      palette,
      vocabulary,
      state.layout.glyphs,
      fontSize,
      state.cell,
    );
  }

  function drawGlyph(state, glyphIndex, colourRow, cellIndex, alpha) {
    if (alpha < INVISIBLE_ALPHA) return;
    const { context, cell, grid, atlas } = state;
    context.globalAlpha = alpha;
    context.drawImage(
      atlas.atlas,
      glyphIndex * cell.width,
      colourRow * cell.height,
      cell.width,
      cell.height,
      (cellIndex % grid.columnCount) * cell.width,
      Math.floor(cellIndex / grid.columnCount) * cell.height,
      cell.width,
      cell.height,
    );
  }

  function drawWord(state, generation, cellIndex, alpha) {
    const glyphIndex = generation.wordGlyphIndices[cellIndex];
    if (glyphIndex === layoutModule.EMPTY_GLYPH) return;
    drawGlyph(
      state,
      glyphIndex,
      generation.wordColourIndices[cellIndex],
      cellIndex,
      alpha * generation.wordBrightness[cellIndex],
    );
  }

  function drawNoise(state, generation, cellIndex, alpha) {
    const glyphIndex = generation.noiseGlyphIndices[cellIndex];
    if (glyphIndex === layoutModule.EMPTY_GLYPH) return;
    drawGlyph(
      state,
      glyphIndex,
      state.atlas.noiseRowIndex,
      cellIndex,
      alpha * NOISE_ALPHA,
    );
  }

  function paintFrame(state, fieldSeconds) {
    const { context, canvasElement, envelope, layout } = state;
    const moment = timeline.resolveGenerationMoment(fieldSeconds);
    const outgoing = layout.generations[moment.generationIndex];
    const incoming = layout.generations[moment.incomingGenerationIndex];
    context.globalAlpha = 1;
    context.fillStyle = palette.backgroundHex;
    context.fillRect(0, 0, canvasElement.width, canvasElement.height);
    for (
      let cellIndex = 0;
      cellIndex < outgoing.clearingOrder.length;
      cellIndex += 1
    ) {
      timeline.writeCellEnvelope(
        envelope,
        moment.phase,
        outgoing.clearingOrder[cellIndex],
        incoming.clearingOrder[cellIndex],
      );
      drawWord(state, outgoing, cellIndex, envelope[timeline.OUTGOING_WORD]);
      drawNoise(state, outgoing, cellIndex, envelope[timeline.OUTGOING_NOISE]);
      drawNoise(state, incoming, cellIndex, envelope[timeline.INCOMING_NOISE]);
      drawWord(state, incoming, cellIndex, envelope[timeline.INCOMING_WORD]);
    }
  }

  function createTokenFieldRenderer(canvasElement, options) {
    const state = {
      canvasElement,
      context: canvasElement.getContext("2d", { alpha: false }),
      envelope: new Float32Array(4),
    };
    const recordingOffsetSeconds = options.startSeconds || 0;
    rebuildGrid(state, canvasElement.width, canvasElement.height);
    return {
      resolveRecordingSource: () => ({
        sequence: "token-field",
        durationSeconds: timeline.cycleDurationSeconds,
      }),
      render: (localElapsedSeconds) =>
        paintFrame(state, recordingOffsetSeconds + localElapsedSeconds),
      resize: (pixelWidth, pixelHeight) =>
        rebuildGrid(state, pixelWidth, pixelHeight),
    };
  }

  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  window.AMBIENT_CANVAS_SCENE_FACTORIES["token-field"] =
    createTokenFieldRenderer;
})();
