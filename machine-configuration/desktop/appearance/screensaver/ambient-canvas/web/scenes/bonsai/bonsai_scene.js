const bonsaiPotColorHex = "#6b7280";
const bonsaiGrowthDurationSeconds = 8;
const bonsaiHoldDurationSeconds = 5;
const bonsaiCycleDurationSeconds =
  bonsaiGrowthDurationSeconds + bonsaiHoldDurationSeconds;
function bonsaiAppendPot(state, rootColumn) {
  const potHalfWidth = 4;
  for (let offset = -potHalfWidth; offset <= potHalfWidth; offset += 1) {
    bonsaiPushCell(
      state,
      rootColumn + offset,
      state.rowCount - 2,
      "_",
      bonsaiPotColorHex,
    );
    if (Math.abs(offset) < potHalfWidth) {
      bonsaiPushCell(
        state,
        rootColumn + offset,
        state.rowCount - 1,
        ":",
        bonsaiPotColorHex,
      );
    }
  }
}
function bonsaiGenerateTree(state) {
  state.orderedCells = [];
  const rootColumn = Math.floor(state.columnCount / 2);
  const trunkLife = Math.floor(state.rowCount * 0.8) + 8;
  bonsaiAppendPot(state, rootColumn);
  bonsaiGrowBranch(state, rootColumn, state.rowCount - 3, "trunk", trunkLife);
}
function bonsaiConfigureGrid(state, pixelWidthDevice, pixelHeightDevice) {
  state.columnCount =
    Math.floor(pixelWidthDevice / state.cellWidthDevicePixels) || 1;
  state.rowCount =
    Math.floor(pixelHeightDevice / state.cellHeightDevicePixels) || 1;
  state.drawingContext.font = `${state.fontSizeDevicePixels}px monospace`;
  state.drawingContext.textBaseline = "top";
  bonsaiGenerateTree(state);
}
function bonsaiRenderFrame(state, elapsedSeconds) {
  const cycleIndex = Math.floor(elapsedSeconds / bonsaiCycleDurationSeconds);
  if (cycleIndex !== state.lastCycleIndex) {
    state.lastCycleIndex = cycleIndex;
    bonsaiGenerateTree(state);
  }
  const timeIntoCycleSeconds =
    elapsedSeconds - cycleIndex * bonsaiCycleDurationSeconds;
  const rawProgress = timeIntoCycleSeconds / bonsaiGrowthDurationSeconds;
  const growthProgress = rawProgress > 1 ? 1 : rawProgress;
  const totalCellCount = state.orderedCells.length;
  const revealedCellCount = Math.floor(growthProgress * totalCellCount);
  state.drawingContext.fillStyle = state.backgroundColorHex;
  state.drawingContext.fillRect(
    0,
    0,
    state.canvasElement.width,
    state.canvasElement.height,
  );
  for (let cellIndex = 0; cellIndex < revealedCellCount; cellIndex += 1) {
    const cell = state.orderedCells[cellIndex];
    state.drawingContext.fillStyle = cell.colorHex;
    const pixelX = cell.columnIndex * state.cellWidthDevicePixels;
    const pixelY = cell.rowIndex * state.cellHeightDevicePixels;
    state.drawingContext.fillText(cell.glyph, pixelX, pixelY);
  }
}

(function registerBonsaiScene() {
  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  function createBonsaiRenderer(canvasElement, options) {
    const fontSizeDevicePixels = Math.round(14 * options.devicePixelRatio);
    const state = {
      canvasElement,
      drawingContext: canvasElement.getContext("2d"),
      backgroundColorHex: window.AmbientCanvasPalette.backgroundHex,
      fontSizeDevicePixels,
      cellWidthDevicePixels: Math.round(fontSizeDevicePixels * 0.6),
      cellHeightDevicePixels: Math.round(fontSizeDevicePixels * 1.05),
      columnCount: 1,
      rowCount: 1,
      orderedCells: [],
      lastCycleIndex: 0,
    };
    bonsaiConfigureGrid(state, canvasElement.width, canvasElement.height);
    return {
      render: (elapsedSeconds) => bonsaiRenderFrame(state, elapsedSeconds),
      resize: (pixelWidthDevice, pixelHeightDevice) =>
        bonsaiConfigureGrid(state, pixelWidthDevice, pixelHeightDevice),
    };
  }
  window.AMBIENT_CANVAS_SCENE_FACTORIES["bonsai"] = createBonsaiRenderer;
})();
