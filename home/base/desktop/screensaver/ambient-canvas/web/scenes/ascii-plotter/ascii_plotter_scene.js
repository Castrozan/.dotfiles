(function registerAsciiPlotterScene() {
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

  function createAsciiPlotterRenderer(canvasElement) {
    const schematic = window.AmbientCanvasAsciiPlotterSchematic;
    const drawingContext = canvasElement.getContext("2d");
    let cellHeightPixels = 1;
    let cellWidthPixels = 1;
    let columnCount = 1;
    let visibleRowCount = 1;

    function resize(pixelWidthDevice, pixelHeightDevice) {
      cellHeightPixels = Math.max(6, pixelHeightDevice / TARGET_VISIBLE_ROWS);
      const fontSizePixels = Math.round(
        cellHeightPixels / CELL_HEIGHT_TO_FONT_RATIO,
      );
      cellWidthPixels = fontSizePixels * CELL_WIDTH_TO_FONT_RATIO;
      columnCount = Math.floor(pixelWidthDevice / cellWidthPixels) || 1;
      visibleRowCount = Math.ceil(pixelHeightDevice / cellHeightPixels) + 1;
      drawingContext.font = fontSizePixels + "px monospace";
      drawingContext.textBaseline = "top";
    }

    function whiteAtAlpha(alpha) {
      return "rgba(255, 255, 255, " + Math.min(1, alpha).toFixed(3) + ")";
    }

    function paintLatticeRow(sourceRow, verticalPixel, alpha) {
      drawingContext.fillStyle = whiteAtAlpha(alpha);
      for (let column = 0; column < columnCount; column += 1) {
        const glyph = schematic.latticeGlyph(column, sourceRow);
        if (glyph) {
          drawingContext.fillText(
            glyph,
            column * cellWidthPixels,
            verticalPixel,
          );
        }
      }
    }

    function paintStructureRow(sourceRow, verticalPixel, alpha) {
      const marks = schematic.buildRowMarks(sourceRow, columnCount);
      for (let index = 0; index < marks.length; index += 1) {
        const mark = marks[index];
        drawingContext.fillStyle = whiteAtAlpha(alpha * mark.weight);
        drawingContext.fillText(
          mark.glyph,
          mark.column * cellWidthPixels,
          verticalPixel,
        );
      }
    }

    function render(elapsedSeconds) {
      drawingContext.fillStyle = "#000000";
      drawingContext.fillRect(0, 0, canvasElement.width, canvasElement.height);

      const emittedRows =
        PRE_ROLL_ROWS + elapsedSeconds * ROWS_EMITTED_PER_SECOND;
      const newestSourceRow = Math.floor(emittedRows);
      const subRowOffset = emittedRows - newestSourceRow;

      for (let screenRow = 0; screenRow < visibleRowCount; screenRow += 1) {
        const sourceRow = newestSourceRow - screenRow;
        if (sourceRow < 0) {
          continue;
        }
        const verticalPixel = (screenRow + subRowOffset) * cellHeightPixels;
        const emissionGlow = Math.exp(-screenRow / EMISSION_GLOW_ROWS);
        const settled = Math.exp(-screenRow / SETTLED_FADE_ROWS);
        paintLatticeRow(
          sourceRow,
          verticalPixel,
          RESIDUAL_LATTICE_ALPHA + EMISSION_LATTICE_ALPHA * emissionGlow,
        );
        paintStructureRow(
          sourceRow,
          verticalPixel,
          RESIDUAL_STRUCTURE_ALPHA +
            SETTLED_STRUCTURE_ALPHA * settled +
            EMISSION_STRUCTURE_ALPHA * emissionGlow,
        );
      }
    }

    resize(canvasElement.width, canvasElement.height);
    return { render, resize };
  }

  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  window.AMBIENT_CANVAS_SCENE_FACTORIES["ascii-plotter"] =
    createAsciiPlotterRenderer;
})();
