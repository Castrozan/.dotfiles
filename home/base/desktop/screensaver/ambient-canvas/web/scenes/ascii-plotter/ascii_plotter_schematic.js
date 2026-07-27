window.AmbientCanvasAsciiPlotterSchematic =
  (function buildAsciiPlotterSchematic() {
    const traces = window.AmbientCanvasAsciiPlotterTraces;
    const BUS_ROW_PROBABILITY = 0.16;
    const SHORTEST_BUS_SHARE = 0.22;
    const LONGEST_BUS_SHARE = 0.82;
    const BUS_WEIGHT = 0.6;
    const LATTICE_COLUMN_PERIOD = 9;
    const LATTICE_ROW_PERIOD = 3;
    const LATTICE_OCCUPANCY = 0.4;
    const LATTICE_GLYPHS = ["·", ":", "|", "-"];

    function pushBusMarks(marks, sourceRow, columnCount) {
      if (traces.hashedUnitInterval(sourceRow, 4241) >= BUS_ROW_PROBABILITY) {
        return;
      }
      const share =
        SHORTEST_BUS_SHARE +
        traces.hashedUnitInterval(sourceRow, 929) *
          (LONGEST_BUS_SHARE - SHORTEST_BUS_SHARE);
      const start = Math.floor(
        traces.hashedUnitInterval(sourceRow, 811) * columnCount * (1 - share),
      );
      const end = Math.min(
        columnCount - 1,
        start + Math.floor(share * columnCount),
      );
      const occupiedColumns = {};
      for (let index = 0; index < marks.length; index += 1) {
        occupiedColumns[marks[index].column] = true;
      }
      for (let column = start; column <= end; column += 1) {
        traces.pushMarkWithinField(
          marks,
          column,
          occupiedColumns[column] ? "┼" : "─",
          BUS_WEIGHT,
          columnCount,
        );
      }
    }

    function buildRowMarks(sourceRow, columnCount) {
      const marks = [];
      const traceCount = traces.traceCountForField(columnCount);
      for (let traceIndex = 0; traceIndex < traceCount; traceIndex += 1) {
        traces.pushTraceMarks(marks, traceIndex, sourceRow, columnCount);
      }
      pushBusMarks(marks, sourceRow, columnCount);
      return marks;
    }

    function latticeGlyph(column, sourceRow) {
      const onLattice =
        column % LATTICE_COLUMN_PERIOD === 0 ||
        sourceRow % LATTICE_ROW_PERIOD === 0;
      if (!onLattice) {
        return null;
      }
      const occupied =
        traces.hashedUnitInterval(column * 733 + 17, sourceRow * 197 + 29) <=
        LATTICE_OCCUPANCY;
      if (!occupied) {
        return null;
      }
      const pick = traces.hashedUnitInterval(
        column * 53 + 7,
        sourceRow * 311 + 3,
      );
      return LATTICE_GLYPHS[Math.floor(pick * LATTICE_GLYPHS.length)];
    }

    return { buildRowMarks, latticeGlyph };
  })();
