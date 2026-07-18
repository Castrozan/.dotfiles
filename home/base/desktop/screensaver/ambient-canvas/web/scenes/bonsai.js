(function registerBonsaiScene() {
  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  function createBonsaiRenderer(canvasElement, options) {
    const drawingContext = canvasElement.getContext("2d");
    const backgroundColorHex = "#0a1a2f";
    const woodColorHex = "#b5844a";
    const potColorHex = "#6b7280";
    const leafColorPalette = ["#4fbf5f", "#5fcf6f", "#6fdf7f", "#7fe88f"];
    const fontSizeDevicePixels = Math.round(14 * options.devicePixelRatio);
    const cellWidthDevicePixels = Math.round(fontSizeDevicePixels * 0.6);
    const cellHeightDevicePixels = Math.round(fontSizeDevicePixels * 1.05);
    const growthDurationSeconds = 8;
    const holdDurationSeconds = 5;
    const cycleDurationSeconds = growthDurationSeconds + holdDurationSeconds;
    let columnCount = 1;
    let rowCount = 1;
    let orderedCells = [];
    let lastCycleIndex = 0;
    function isInsideGrid(columnIndex, rowIndex) {
      return (
        columnIndex >= 0 &&
        columnIndex < columnCount &&
        rowIndex >= 0 &&
        rowIndex < rowCount
      );
    }
    function pushCell(columnIndex, rowIndex, glyph, colorHex) {
      if (isInsideGrid(columnIndex, rowIndex)) {
        orderedCells.push({ columnIndex, rowIndex, glyph, colorHex });
      }
    }
    function randomLeafColorHex() {
      const paletteIndex = Math.floor(Math.random() * leafColorPalette.length);
      return leafColorPalette[paletteIndex];
    }
    function chooseWoodGlyph(columnDelta, rowDelta) {
      if (rowDelta === 0) return "~";
      if (columnDelta < 0) return "\\";
      if (columnDelta > 0) return "/";
      return "|";
    }
    function chooseGrowthDelta(branchType, remainingLife) {
      let columnDelta = Math.floor(Math.random() * 3) - 1;
      let rowDelta = 0;
      if (branchType === "trunk") {
        if (remainingLife > 3) rowDelta = Math.random() < 0.7 ? -1 : 0;
      } else if (branchType === "shootLeft") {
        columnDelta = Math.random() < 0.7 ? -1 : 0;
        rowDelta = Math.random() < 0.5 ? -1 : 0;
      } else if (branchType === "shootRight") {
        columnDelta = Math.random() < 0.7 ? 1 : 0;
        rowDelta = Math.random() < 0.5 ? -1 : 0;
      } else {
        rowDelta = Math.random() < 0.3 ? -1 : 0;
      }
      return { columnDelta, rowDelta };
    }
    function appendLeafCluster(centerColumn, centerRow) {
      const clusterSize = 3 + Math.floor(Math.random() * 4);
      for (let leafIndex = 0; leafIndex < clusterSize; leafIndex += 1) {
        const columnIndex = centerColumn + Math.floor(Math.random() * 3) - 1;
        const rowIndex = centerRow + Math.floor(Math.random() * 3) - 1;
        const glyph = Math.random() < 0.5 ? "&" : "*";
        pushCell(columnIndex, rowIndex, glyph, randomLeafColorHex());
      }
    }
    function growBranch(startColumn, startRow, branchType, initialLife) {
      let columnIndex = startColumn;
      let rowIndex = startRow;
      let remainingLife = initialLife;
      while (remainingLife > 0) {
        remainingLife -= 1;
        const delta = chooseGrowthDelta(branchType, remainingLife);
        const canSpawnShoot = branchType === "trunk" && remainingLife > 4;
        if (canSpawnShoot && Math.random() < 0.14) {
          const shootType = Math.random() < 0.5 ? "shootLeft" : "shootRight";
          const shootLife = Math.floor(remainingLife * 0.5) + 2;
          growBranch(columnIndex, rowIndex, shootType, shootLife);
        }
        columnIndex += delta.columnDelta;
        rowIndex += delta.rowDelta;
        if (!isInsideGrid(columnIndex, rowIndex)) break;
        if (remainingLife < 3) {
          appendLeafCluster(columnIndex, rowIndex);
        } else {
          const glyph = chooseWoodGlyph(delta.columnDelta, delta.rowDelta);
          pushCell(columnIndex, rowIndex, glyph, woodColorHex);
        }
      }
    }
    function appendPot(rootColumn) {
      const potHalfWidth = 4;
      for (let offset = -potHalfWidth; offset <= potHalfWidth; offset += 1) {
        pushCell(rootColumn + offset, rowCount - 2, "_", potColorHex);
        if (Math.abs(offset) < potHalfWidth) {
          pushCell(rootColumn + offset, rowCount - 1, ":", potColorHex);
        }
      }
    }
    function generateTree() {
      orderedCells = [];
      const rootColumn = Math.floor(columnCount / 2);
      const trunkLife = Math.floor(rowCount * 0.8) + 8;
      appendPot(rootColumn);
      growBranch(rootColumn, rowCount - 3, "trunk", trunkLife);
    }
    function configureGrid(pixelWidthDevice, pixelHeightDevice) {
      columnCount = Math.floor(pixelWidthDevice / cellWidthDevicePixels) || 1;
      rowCount = Math.floor(pixelHeightDevice / cellHeightDevicePixels) || 1;
      drawingContext.font = fontSizeDevicePixels + "px monospace";
      drawingContext.textBaseline = "top";
      generateTree();
    }
    function render(elapsedSeconds) {
      const cycleIndex = Math.floor(elapsedSeconds / cycleDurationSeconds);
      if (cycleIndex !== lastCycleIndex) {
        lastCycleIndex = cycleIndex;
        generateTree();
      }
      const timeIntoCycleSeconds =
        elapsedSeconds - cycleIndex * cycleDurationSeconds;
      const rawProgress = timeIntoCycleSeconds / growthDurationSeconds;
      const growthProgress = rawProgress > 1 ? 1 : rawProgress;
      const totalCellCount = orderedCells.length;
      const revealedCellCount = Math.floor(growthProgress * totalCellCount);
      drawingContext.fillStyle = backgroundColorHex;
      drawingContext.fillRect(0, 0, canvasElement.width, canvasElement.height);
      for (let cellIndex = 0; cellIndex < revealedCellCount; cellIndex += 1) {
        const cell = orderedCells[cellIndex];
        drawingContext.fillStyle = cell.colorHex;
        const pixelX = cell.columnIndex * cellWidthDevicePixels;
        const pixelY = cell.rowIndex * cellHeightDevicePixels;
        drawingContext.fillText(cell.glyph, pixelX, pixelY);
      }
    }
    function resize(pixelWidthDevice, pixelHeightDevice) {
      configureGrid(pixelWidthDevice, pixelHeightDevice);
    }
    configureGrid(canvasElement.width, canvasElement.height);
    return { render, resize };
  }
  window.AMBIENT_CANVAS_SCENE_FACTORIES["bonsai"] = createBonsaiRenderer;
})();
