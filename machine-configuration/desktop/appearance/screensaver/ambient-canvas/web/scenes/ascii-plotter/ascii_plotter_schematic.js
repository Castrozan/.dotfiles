const asciiPlotterTraces = window.AmbientCanvasAsciiPlotterTraces;
const BUS_ROW_PROBABILITY = 0.16;
const SHORTEST_BUS_SHARE = 0.22;
const LONGEST_BUS_SHARE = 0.82;
const BUS_WEIGHT = 0.6;
const LATTICE_COLUMN_PERIOD = 9;
const LATTICE_ROW_PERIOD = 3;
const LATTICE_OCCUPANCY = 0.4;
const LATTICE_GLYPHS = ["·", ":", "|", "-"];

function busShareOfField(sourceRow) {
  return (
    SHORTEST_BUS_SHARE +
    asciiPlotterTraces.hashedUnitInterval(sourceRow, 929) *
      (LONGEST_BUS_SHARE - SHORTEST_BUS_SHARE)
  );
}

function collectMarkedColumns(marks) {
  return new Set(marks.map((mark) => mark.column));
}

function pushBusMarks(marks, sourceRow, columnCount) {
  if (
    asciiPlotterTraces.hashedUnitInterval(sourceRow, 4241) >=
    BUS_ROW_PROBABILITY
  ) {
    return;
  }
  const share = busShareOfField(sourceRow);
  const start = Math.floor(
    asciiPlotterTraces.hashedUnitInterval(sourceRow, 811) *
      columnCount *
      (1 - share),
  );
  const end = Math.min(
    columnCount - 1,
    start + Math.floor(share * columnCount),
  );
  const occupiedColumns = collectMarkedColumns(marks);
  for (let column = start; column <= end; column += 1) {
    asciiPlotterTraces.pushMarkWithinField(
      marks,
      column,
      occupiedColumns.has(column) ? "┼" : "─",
      BUS_WEIGHT,
      columnCount,
    );
  }
}

function buildRowMarks(sourceRow, columnCount) {
  const marks = [];
  const traceCount = asciiPlotterTraces.traceCountForField(columnCount);
  for (let traceIndex = 0; traceIndex < traceCount; traceIndex += 1) {
    asciiPlotterTraces.pushTraceMarks(
      marks,
      traceIndex,
      sourceRow,
      columnCount,
    );
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
    asciiPlotterTraces.hashedUnitInterval(
      column * 733 + 17,
      sourceRow * 197 + 29,
    ) <= LATTICE_OCCUPANCY;
  if (!occupied) {
    return null;
  }
  const pick = asciiPlotterTraces.hashedUnitInterval(
    column * 53 + 7,
    sourceRow * 311 + 3,
  );
  return LATTICE_GLYPHS[Math.floor(pick * LATTICE_GLYPHS.length)];
}

window.AmbientCanvasAsciiPlotterSchematic =
  (function buildAsciiPlotterSchematic() {
    return { buildRowMarks, latticeGlyph };
  })();
