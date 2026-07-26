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

    function measureAxisOffsets(cellCount, cellsPerPanel, gap, gutter) {
      const offsets = new Float64Array(cellCount);
      for (let cellIndex = 0; cellIndex < cellCount; cellIndex += 1) {
        const panelIndex = Math.floor(cellIndex / cellsPerPanel);
        offsets[cellIndex] =
          cellIndex * (1 + gap) - panelIndex * gap + panelIndex * gutter;
      }
      return offsets;
    }

    function measureAxisExtent(cellCount, panelCount, gap, gutter) {
      return (
        cellCount + (cellCount - panelCount) * gap + (panelCount - 1) * gutter
      );
    }

    function resolveDisplayWallLayout(pixelWidthDevice, pixelHeightDevice) {
      const widthInCellWidths = measureAxisExtent(
        displayColumns,
        PANEL_COLUMNS,
        DISPLAY_GAP_IN_CELL_WIDTHS,
        PANEL_GUTTER_IN_CELL_WIDTHS,
      );
      const heightInCellHeights = measureAxisExtent(
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
      const columnOffsets = measureAxisOffsets(
        displayColumns,
        DISPLAY_COLUMNS_PER_PANEL,
        DISPLAY_GAP_IN_CELL_WIDTHS,
        PANEL_GUTTER_IN_CELL_WIDTHS,
      );
      const rowOffsets = measureAxisOffsets(
        displayRows,
        DISPLAY_ROWS_PER_PANEL,
        DISPLAY_GAP_IN_CELL_HEIGHTS,
        PANEL_GUTTER_IN_CELL_HEIGHTS,
      );
      const cellOriginXs = new Float64Array(displayCount);
      const cellOriginYs = new Float64Array(displayCount);
      const segmentFieldXs = new Float32Array(displayCount * segmentCount);
      const segmentFieldYs = new Float32Array(displayCount * segmentCount);

      for (let rowIndex = 0; rowIndex < displayRows; rowIndex += 1) {
        for (
          let columnIndex = 0;
          columnIndex < displayColumns;
          columnIndex += 1
        ) {
          const cellIndex = rowIndex * displayColumns + columnIndex;
          const originX =
            gridOriginX + columnOffsets[columnIndex] * cellPixelWidth;
          const originY = gridOriginY + rowOffsets[rowIndex] * cellPixelHeight;
          cellOriginXs[cellIndex] = originX;
          cellOriginYs[cellIndex] = originY;
          for (let segment = 0; segment < segmentCount; segment += 1) {
            const segmentAxis = geometry.segmentAxes[segment];
            segmentFieldXs[cellIndex * segmentCount + segment] =
              (originX +
                geometry.measureSegmentCenterX(segmentAxis) * cellPixelWidth) /
              pixelWidthDevice;
            segmentFieldYs[cellIndex * segmentCount + segment] =
              (originY +
                geometry.measureSegmentCenterY(segmentAxis) * cellPixelHeight) /
              pixelHeightDevice;
          }
        }
      }

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
