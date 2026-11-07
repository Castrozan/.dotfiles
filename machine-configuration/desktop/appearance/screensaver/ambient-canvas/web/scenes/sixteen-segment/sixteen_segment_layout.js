function sixteenSegmentLayoutMeasureAxisOffsets(cellCount, cellsPerPanel, gap, gutter) {
  const offsets = new Float64Array(cellCount);
  for (let cellIndex = 0; cellIndex < cellCount; cellIndex += 1) {
    const panelIndex = Math.floor(cellIndex / cellsPerPanel);
    offsets[cellIndex] =
      cellIndex * (1 + gap) - panelIndex * gap + panelIndex * gutter;
  }
  return offsets;
}

function sixteenSegmentLayoutMeasureAxisExtent(cellCount, panelCount, gap, gutter) {
  return cellCount + (cellCount - panelCount) * gap + (panelCount - 1) * gutter;
}

function sixteenSegmentLayoutFillCellOrigins(
  cellOriginXs,
  cellOriginYs,
  columnOriginXs,
  rowOriginYs,
) {
  for (let rowIndex = 0; rowIndex < rowOriginYs.length; rowIndex += 1) {
    for (
      let columnIndex = 0;
      columnIndex < columnOriginXs.length;
      columnIndex += 1
    ) {
      const cellIndex = rowIndex * columnOriginXs.length + columnIndex;
      cellOriginXs[cellIndex] = columnOriginXs[columnIndex];
      cellOriginYs[cellIndex] = rowOriginYs[rowIndex];
    }
  }
}

function sixteenSegmentLayoutFillSegmentFieldAxis(
  segmentFieldAxis,
  cellOriginAxis,
  segmentOffsetAxis,
  pixelExtentDevice,
) {
  const segmentCount = segmentOffsetAxis.length;
  for (let cellIndex = 0; cellIndex < cellOriginAxis.length; cellIndex += 1) {
    for (let segment = 0; segment < segmentCount; segment += 1) {
      segmentFieldAxis[cellIndex * segmentCount + segment] =
        (cellOriginAxis[cellIndex] + segmentOffsetAxis[segment]) /
        pixelExtentDevice;
    }
  }
}

window.AmbientCanvasSixteenSegmentLayout =
  (function buildSixteenSegmentLayout() {
    const DISPLAY_COLUMNS_PER_PANEL = 8;
    const DISPLAY_ROWS_PER_PANEL = 4;
    const PANEL_COLUMNS = 4;
    const PANEL_ROWS = 3;
    const DISPLAY_WIDTH_OVER_HEIGHT = 0.62;
    const DISPLAY_GAP_IN_CELL_WIDTHS = 0.3;
    const DISPLAY_GAP_IN_CELL_HEIGHTS = 0.22;
    const PANEL_GUTTER_IN_CELL_WIDTHS = 0.95;
    const PANEL_GUTTER_IN_CELL_HEIGHTS = 0.7;
    const GRID_FILL_FRACTION = 0.94;

    const geometry = window.AmbientCanvasSixteenSegmentGeometry;
    const displayColumns = PANEL_COLUMNS * DISPLAY_COLUMNS_PER_PANEL;
    const displayRows = PANEL_ROWS * DISPLAY_ROWS_PER_PANEL;
    const displayCount = displayColumns * displayRows;
    const segmentCount = geometry.segmentAxes.length;

    function resolveDisplayWallLayout(pixelWidthDevice, pixelHeightDevice) {
      const widthInCellWidths = sixteenSegmentLayoutMeasureAxisExtent(
        displayColumns,
        PANEL_COLUMNS,
        DISPLAY_GAP_IN_CELL_WIDTHS,
        PANEL_GUTTER_IN_CELL_WIDTHS,
      );
      const heightInCellHeights = sixteenSegmentLayoutMeasureAxisExtent(
        displayRows,
        PANEL_ROWS,
        DISPLAY_GAP_IN_CELL_HEIGHTS,
        PANEL_GUTTER_IN_CELL_HEIGHTS,
      );
      const cellPixelHeight = Math.min(
        (pixelWidthDevice * GRID_FILL_FRACTION) /
          (widthInCellWidths * DISPLAY_WIDTH_OVER_HEIGHT),
        (pixelHeightDevice * GRID_FILL_FRACTION) / heightInCellHeights,
      );
      const cellPixelWidth = cellPixelHeight * DISPLAY_WIDTH_OVER_HEIGHT;
      const gridOriginX =
        (pixelWidthDevice - widthInCellWidths * cellPixelWidth) / 2;
      const gridOriginY =
        (pixelHeightDevice - heightInCellHeights * cellPixelHeight) / 2;
      const columnOriginXs = sixteenSegmentLayoutMeasureAxisOffsets(
        displayColumns,
        DISPLAY_COLUMNS_PER_PANEL,
        DISPLAY_GAP_IN_CELL_WIDTHS,
        PANEL_GUTTER_IN_CELL_WIDTHS,
      ).map((offset) => gridOriginX + offset * cellPixelWidth);
      const rowOriginYs = sixteenSegmentLayoutMeasureAxisOffsets(
        displayRows,
        DISPLAY_ROWS_PER_PANEL,
        DISPLAY_GAP_IN_CELL_HEIGHTS,
        PANEL_GUTTER_IN_CELL_HEIGHTS,
      ).map((offset) => gridOriginY + offset * cellPixelHeight);
      const segmentOffsetXs = geometry.segmentAxes.map(
        (segmentAxis) =>
          geometry.measureSegmentCenterX(segmentAxis) * cellPixelWidth,
      );
      const segmentOffsetYs = geometry.segmentAxes.map(
        (segmentAxis) =>
          geometry.measureSegmentCenterY(segmentAxis) * cellPixelHeight,
      );
      const cellOriginXs = new Float64Array(displayCount);
      const cellOriginYs = new Float64Array(displayCount);
      const segmentFieldXs = new Float32Array(displayCount * segmentCount);
      const segmentFieldYs = new Float32Array(displayCount * segmentCount);

      sixteenSegmentLayoutFillCellOrigins(cellOriginXs, cellOriginYs, columnOriginXs, rowOriginYs);
      sixteenSegmentLayoutFillSegmentFieldAxis(
        segmentFieldXs,
        cellOriginXs,
        segmentOffsetXs,
        pixelWidthDevice,
      );
      sixteenSegmentLayoutFillSegmentFieldAxis(
        segmentFieldYs,
        cellOriginYs,
        segmentOffsetYs,
        pixelHeightDevice,
      );

      return {
        cellPixelWidth,
        cellPixelHeight,
        cellOriginXs,
        cellOriginYs,
        segmentFieldXs,
        segmentFieldYs,
      };
    }

    return { displayCount, segmentCount, resolveDisplayWallLayout };
  })();
