window.AmbientCanvasAsciiPlotterTraces = (function buildAsciiPlotterTraces() {
  const TRACE_SPACING_COLUMNS = 4;
  const TRACE_HOME_MARGIN_COLUMNS = 3;
  const TRACE_JOG_SPAN_COLUMNS = 3;
  const SHORTEST_TRACE_SEGMENT_ROWS = 3;
  const LONGEST_TRACE_SEGMENT_ROWS = 14;
  const TRACE_REST_PROBABILITY = 0.18;
  const COMPONENT_SEGMENT_PROBABILITY = 0.22;
  const SHORTEST_COMPONENT_ROWS = 1;
  const LONGEST_COMPONENT_ROWS = 3;
  const SHORTEST_COMPONENT_COLUMNS = 2;
  const LONGEST_COMPONENT_COLUMNS = 6;
  const SHADE_GLYPHS = ["▒", "▓", "█", "█", "█"];
  const STRUCTURE_WEIGHT = 0.72;
  const COMPONENT_WEIGHT = 1;

  function hashedUnitInterval(first, second) {
    let mixed = Math.imul(first ^ 0x9e3779b9, 0x85ebca6b);
    mixed = Math.imul(mixed ^ (second + 0x165667b1), 0xc2b2ae35);
    mixed ^= mixed >>> 15;
    mixed = Math.imul(mixed, 0x2545f491);
    mixed ^= mixed >>> 13;
    return (mixed >>> 0) / 4294967296;
  }

  function traceCountForField(columnCount) {
    return Math.ceil(
      (columnCount - TRACE_HOME_MARGIN_COLUMNS) / TRACE_SPACING_COLUMNS,
    );
  }

  function traceSegmentRows(traceIndex) {
    const span = LONGEST_TRACE_SEGMENT_ROWS - SHORTEST_TRACE_SEGMENT_ROWS;
    return (
      SHORTEST_TRACE_SEGMENT_ROWS +
      Math.floor(hashedUnitInterval(traceIndex, 7717) * span)
    );
  }

  function traceColumnAtSegment(traceIndex, segmentIndex) {
    const homeColumn =
      TRACE_HOME_MARGIN_COLUMNS + traceIndex * TRACE_SPACING_COLUMNS;
    const drift = hashedUnitInterval(traceIndex * 131 + 5, segmentIndex) - 0.5;
    return homeColumn + Math.round(drift * 2 * TRACE_JOG_SPAN_COLUMNS);
  }

  function componentBarAtRow(traceIndex, segmentIndex, rowInSegment) {
    const carriesComponent =
      hashedUnitInterval(traceIndex * 977 + 11, segmentIndex) <
      COMPONENT_SEGMENT_PROBABILITY;
    if (!carriesComponent || rowInSegment < 1) {
      return 0;
    }
    const rowSpan = LONGEST_COMPONENT_ROWS - SHORTEST_COMPONENT_ROWS;
    const componentRows =
      SHORTEST_COMPONENT_ROWS +
      Math.floor(
        hashedUnitInterval(traceIndex * 31 + 3, segmentIndex) * rowSpan,
      );
    if (rowInSegment > componentRows) {
      return 0;
    }
    const columnSpan = LONGEST_COMPONENT_COLUMNS - SHORTEST_COMPONENT_COLUMNS;
    return (
      SHORTEST_COMPONENT_COLUMNS +
      Math.floor(
        hashedUnitInterval(traceIndex * 17 + 9, segmentIndex * 3 + 1) *
          columnSpan,
      )
    );
  }

  function shadeGlyphFor(traceIndex, segmentIndex, rowInSegment) {
    const pick = hashedUnitInterval(
      traceIndex * 61 + rowInSegment,
      segmentIndex * 7 + 13,
    );
    return SHADE_GLYPHS[Math.floor(pick * SHADE_GLYPHS.length)];
  }

  function pushMarkWithinField(marks, column, glyph, weight, columnCount) {
    if (column < 0 || column >= columnCount) {
      return;
    }
    marks.push({ column, glyph, weight });
  }

  function pushJogMarks(marks, previousColumn, column, columnCount) {
    const movingRight = column > previousColumn;
    const leftmost = Math.min(previousColumn, column);
    const rightmost = Math.max(previousColumn, column);
    for (let run = leftmost + 1; run < rightmost; run += 1) {
      pushMarkWithinField(marks, run, "─", STRUCTURE_WEIGHT, columnCount);
    }
    pushMarkWithinField(
      marks,
      previousColumn,
      movingRight ? "╰" : "╯",
      STRUCTURE_WEIGHT,
      columnCount,
    );
    pushMarkWithinField(
      marks,
      column,
      movingRight ? "╮" : "╭",
      STRUCTURE_WEIGHT,
      columnCount,
    );
  }

  function traceRestsThroughSegment(traceIndex, segmentIndex) {
    return (
      hashedUnitInterval(traceIndex * 7 + 1, segmentIndex * 5 + 2) <
      TRACE_REST_PROBABILITY
    );
  }

  function pushTraceMarks(marks, traceIndex, sourceRow, columnCount) {
    const segmentRows = traceSegmentRows(traceIndex);
    const segmentIndex = Math.floor(sourceRow / segmentRows);
    if (traceRestsThroughSegment(traceIndex, segmentIndex)) {
      return;
    }
    const rowInSegment = sourceRow - segmentIndex * segmentRows;
    const column = traceColumnAtSegment(traceIndex, segmentIndex);

    if (rowInSegment === 0 && segmentIndex > 0) {
      const previousColumn = traceColumnAtSegment(traceIndex, segmentIndex - 1);
      if (previousColumn === column) {
        pushMarkWithinField(marks, column, "│", STRUCTURE_WEIGHT, columnCount);
        return;
      }
      pushJogMarks(marks, previousColumn, column, columnCount);
      return;
    }

    const componentColumns = componentBarAtRow(
      traceIndex,
      segmentIndex,
      rowInSegment,
    );
    if (componentColumns > 0) {
      const shade = shadeGlyphFor(traceIndex, segmentIndex, rowInSegment);
      for (let offset = 0; offset < componentColumns; offset += 1) {
        pushMarkWithinField(
          marks,
          column + offset,
          shade,
          COMPONENT_WEIGHT,
          columnCount,
        );
      }
      return;
    }
    pushMarkWithinField(marks, column, "│", STRUCTURE_WEIGHT, columnCount);
  }

  return {
    hashedUnitInterval,
    traceCountForField,
    pushMarkWithinField,
    pushTraceMarks,
  };
})();
