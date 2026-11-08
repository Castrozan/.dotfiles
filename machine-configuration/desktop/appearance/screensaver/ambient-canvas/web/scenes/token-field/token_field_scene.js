const tokenFieldTargetVisibleRows = 44;
const tokenFieldSmallestRowHeightPixels = 10;
const tokenFieldFontSizeToRowHeight = 0.76;
const tokenFieldNoiseAlpha = 0.6;
const tokenFieldInvisibleAlpha = 0.004;

function tokenFieldRebuildGrid(state, pixelWidth, pixelHeight) {
  const rowHeight = Math.max(
    tokenFieldSmallestRowHeightPixels,
    Math.floor(pixelHeight / tokenFieldTargetVisibleRows),
  );
  const fontSizePixels = Math.round(rowHeight * tokenFieldFontSizeToRowHeight);
  const glyphAtlas = window.AmbientCanvasTokenFieldGlyphAtlas;
  const vocabulary = window.AmbientCanvasTokenFieldVocabulary;
  state.cell = glyphAtlas.measureGlyphCell(fontSizePixels, rowHeight);
  state.grid = {
    columnCount: Math.ceil(pixelWidth / state.cell.width),
    rowCount: Math.ceil(pixelHeight / state.cell.height),
  };
  state.layout = window.AmbientCanvasTokenFieldLayout.buildTokenFieldLayout(
    state.grid,
    window.AmbientCanvasTokenFieldTimeline.GENERATION_COUNT,
    vocabulary,
  );
  state.atlas = glyphAtlas.buildGlyphAtlas({
    palette: window.AmbientCanvasPalette,
    vocabulary,
    glyphs: state.layout.glyphs,
    fontSizePixels,
    cell: state.cell,
  });
}

function tokenFieldDrawGlyph(state, glyphIndex, colourRow, cellIndex, alpha) {
  if (alpha < tokenFieldInvisibleAlpha) return;
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

function tokenFieldDrawWord(state, generation, cellIndex, alpha) {
  const glyphIndex = generation.wordGlyphIndices[cellIndex];
  if (glyphIndex === window.AmbientCanvasTokenFieldLayout.EMPTY_GLYPH) return;
  tokenFieldDrawGlyph(
    state,
    glyphIndex,
    generation.wordColourIndices[cellIndex],
    cellIndex,
    alpha * generation.wordBrightness[cellIndex],
  );
}

function tokenFieldDrawNoise(state, generation, cellIndex, alpha) {
  const glyphIndex = generation.noiseGlyphIndices[cellIndex];
  if (glyphIndex === window.AmbientCanvasTokenFieldLayout.EMPTY_GLYPH) return;
  tokenFieldDrawGlyph(
    state,
    glyphIndex,
    state.atlas.noiseRowIndex,
    cellIndex,
    alpha * tokenFieldNoiseAlpha,
  );
}

function tokenFieldPaintFrame(state, fieldSeconds) {
  const { context, canvasElement, envelope, layout } = state;
  const timeline = window.AmbientCanvasTokenFieldTimeline;
  const moment = timeline.resolveGenerationMoment(fieldSeconds);
  const outgoing = layout.generations[moment.generationIndex];
  const incoming = layout.generations[moment.incomingGenerationIndex];
  context.globalAlpha = 1;
  context.fillStyle = window.AmbientCanvasPalette.backgroundHex;
  context.fillRect(0, 0, canvasElement.width, canvasElement.height);
  for (let index = 0; index < outgoing.clearingOrder.length; index += 1) {
    timeline.writeCellEnvelope(
      envelope,
      moment.phase,
      outgoing.clearingOrder[index],
      incoming.clearingOrder[index],
    );
    tokenFieldDrawWord(
      state,
      outgoing,
      index,
      envelope[timeline.OUTGOING_WORD],
    );
    tokenFieldDrawNoise(
      state,
      outgoing,
      index,
      envelope[timeline.OUTGOING_NOISE],
    );
    tokenFieldDrawNoise(
      state,
      incoming,
      index,
      envelope[timeline.INCOMING_NOISE],
    );
    tokenFieldDrawWord(
      state,
      incoming,
      index,
      envelope[timeline.INCOMING_WORD],
    );
  }
}

function tokenFieldCreateRenderer(canvasElement, options) {
  const state = {
    canvasElement,
    context: canvasElement.getContext("2d", { alpha: false }),
    envelope: new Float32Array(4),
  };
  const recordingOffsetSeconds = options.startSeconds || 0;
  tokenFieldRebuildGrid(state, canvasElement.width, canvasElement.height);
  return {
    resolveRecordingSource: () => ({
      sequence: "token-field",
      durationSeconds:
        window.AmbientCanvasTokenFieldTimeline.cycleDurationSeconds,
    }),
    render: (localElapsedSeconds) =>
      tokenFieldPaintFrame(state, recordingOffsetSeconds + localElapsedSeconds),
    resize: (pixelWidth, pixelHeight) =>
      tokenFieldRebuildGrid(state, pixelWidth, pixelHeight),
  };
}

window.AMBIENT_CANVAS_SCENE_FACTORIES =
  window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
window.AMBIENT_CANVAS_SCENE_FACTORIES["token-field"] = tokenFieldCreateRenderer;
