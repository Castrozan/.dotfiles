window.AmbientCanvasBrailleFrameRenderer =
  (function buildBrailleFrameRenderer() {
    const BRAILLE_PATTERN_BASE_CODE_POINT = 0x2800;
    const BRAILLE_DOT_BIT_BY_ROW_AND_COLUMN = [
      [0x01, 0x08],
      [0x02, 0x10],
      [0x04, 0x20],
      [0x40, 0x80],
    ];
    const BRAILLE_DOT_COLUMNS_PER_CELL = 2;
    const BRAILLE_DOT_ROWS_PER_CELL = 4;
    const FULLY_RAISED_BRAILLE_CELL = "⣿";

    function resolveGlyphGrid(
      displayContext,
      canvasElement,
      characterRows,
      glyphFontFamily,
    ) {
      const fontSize = canvasElement.height / characterRows;
      displayContext.font = fontSize + "px " + glyphFontFamily;
      const advanceWidth =
        displayContext.measureText(FULLY_RAISED_BRAILLE_CELL).width || fontSize;
      return {
        fontSize: fontSize,
        advanceWidth: advanceWidth,
        characterRows: characterRows,
        characterColumns: Math.max(
          1,
          Math.floor(canvasElement.width / advanceWidth),
        ),
        dotPixelWidth: advanceWidth / BRAILLE_DOT_COLUMNS_PER_CELL,
        dotPixelHeight: fontSize / BRAILLE_DOT_ROWS_PER_CELL,
      };
    }

    function drawSourceIntoDotGrid(
      samplingContext,
      imageSource,
      sourcePixelWidth,
      sourcePixelHeight,
      glyphGrid,
    ) {
      const dotColumns =
        glyphGrid.characterColumns * BRAILLE_DOT_COLUMNS_PER_CELL;
      const dotRows = glyphGrid.characterRows * BRAILLE_DOT_ROWS_PER_CELL;
      samplingContext.fillStyle = "#000000";
      samplingContext.fillRect(0, 0, dotColumns, dotRows);
      const fittedScale = Math.min(
        (dotColumns * glyphGrid.dotPixelWidth) / sourcePixelWidth,
        (dotRows * glyphGrid.dotPixelHeight) / sourcePixelHeight,
      );
      const drawnDotWidth =
        (sourcePixelWidth * fittedScale) / glyphGrid.dotPixelWidth;
      const drawnDotHeight =
        (sourcePixelHeight * fittedScale) / glyphGrid.dotPixelHeight;
      samplingContext.drawImage(
        imageSource,
        (dotColumns - drawnDotWidth) / 2,
        (dotRows - drawnDotHeight) / 2,
        drawnDotWidth,
        drawnDotHeight,
      );
    }

    function resolveBrailleCellCodePoint(
      dotPixels,
      dotColumns,
      characterRow,
      characterColumn,
      luminanceThreshold,
    ) {
      let raisedDotBits = 0;
      for (let dotRow = 0; dotRow < BRAILLE_DOT_ROWS_PER_CELL; dotRow += 1) {
        for (
          let dotColumn = 0;
          dotColumn < BRAILLE_DOT_COLUMNS_PER_CELL;
          dotColumn += 1
        ) {
          const sampleX =
            characterColumn * BRAILLE_DOT_COLUMNS_PER_CELL + dotColumn;
          const sampleY = characterRow * BRAILLE_DOT_ROWS_PER_CELL + dotRow;
          const sampleOffset = (sampleY * dotColumns + sampleX) * 4;
          const luminance =
            (dotPixels[sampleOffset] * 0.2126 +
              dotPixels[sampleOffset + 1] * 0.7152 +
              dotPixels[sampleOffset + 2] * 0.0722) /
            255;
          if (luminance >= luminanceThreshold) {
            raisedDotBits |=
              BRAILLE_DOT_BIT_BY_ROW_AND_COLUMN[dotRow][dotColumn];
          }
        }
      }
      return BRAILLE_PATTERN_BASE_CODE_POINT + raisedDotBits;
    }

    function paintBrailleGlyphs(
      displayContext,
      canvasElement,
      glyphGrid,
      dotPixels,
      appearance,
    ) {
      const dotColumns =
        glyphGrid.characterColumns * BRAILLE_DOT_COLUMNS_PER_CELL;
      displayContext.fillStyle = appearance.glyphColor;
      displayContext.textBaseline = "top";
      const horizontalInset =
        (canvasElement.width -
          glyphGrid.characterColumns * glyphGrid.advanceWidth) /
        2;
      for (
        let characterRow = 0;
        characterRow < glyphGrid.characterRows;
        characterRow += 1
      ) {
        let glyphRowText = "";
        for (
          let characterColumn = 0;
          characterColumn < glyphGrid.characterColumns;
          characterColumn += 1
        ) {
          glyphRowText += String.fromCharCode(
            resolveBrailleCellCodePoint(
              dotPixels,
              dotColumns,
              characterRow,
              characterColumn,
              appearance.luminanceThreshold,
            ),
          );
        }
        displayContext.fillText(
          glyphRowText,
          horizontalInset,
          characterRow * glyphGrid.fontSize,
        );
      }
    }

    function createBrailleFrameRenderer(canvasElement, appearance) {
      const displayContext = canvasElement.getContext("2d");
      const samplingCanvas = document.createElement("canvas");
      const samplingContext = samplingCanvas.getContext("2d", {
        willReadFrequently: true,
      });

      return function renderBrailleFrame(
        imageSource,
        sourcePixelWidth,
        sourcePixelHeight,
      ) {
        displayContext.fillStyle = appearance.backgroundFillStyle;
        displayContext.fillRect(
          0,
          0,
          canvasElement.width,
          canvasElement.height,
        );
        if (!sourcePixelWidth || !sourcePixelHeight) {
          return;
        }
        const glyphGrid = resolveGlyphGrid(
          displayContext,
          canvasElement,
          appearance.characterRows,
          appearance.glyphFontFamily,
        );
        const dotColumns =
          glyphGrid.characterColumns * BRAILLE_DOT_COLUMNS_PER_CELL;
        const dotRows = glyphGrid.characterRows * BRAILLE_DOT_ROWS_PER_CELL;
        if (
          samplingCanvas.width !== dotColumns ||
          samplingCanvas.height !== dotRows
        ) {
          samplingCanvas.width = dotColumns;
          samplingCanvas.height = dotRows;
        }
        drawSourceIntoDotGrid(
          samplingContext,
          imageSource,
          sourcePixelWidth,
          sourcePixelHeight,
          glyphGrid,
        );
        const dotPixels = samplingContext.getImageData(
          0,
          0,
          dotColumns,
          dotRows,
        ).data;
        paintBrailleGlyphs(
          displayContext,
          canvasElement,
          glyphGrid,
          dotPixels,
          appearance,
        );
      };
    }

    return { createBrailleFrameRenderer: createBrailleFrameRenderer };
  })();
