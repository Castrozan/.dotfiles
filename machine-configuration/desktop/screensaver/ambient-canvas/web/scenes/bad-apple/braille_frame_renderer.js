window.AmbientCanvasBrailleFrameRenderer =
  (function buildBrailleFrameRenderer() {
    const BRAILLE_PATTERN_BASE_CODE_POINT = 0x2800;
    const BRAILLE_DOT_BIT_BY_ROW_AND_COLUMN = [
      [0x01, 0x08],
      [0x02, 0x10],
      [0x04, 0x20],
      [0x40, 0x80],
    ];

    const glyphGridGeometry = window.AmbientCanvasBrailleGlyphGrid;

    function resolveBrailleCellCodePoint(
      dotPixels,
      dotColumns,
      characterRow,
      characterColumn,
      luminanceThreshold,
    ) {
      let raisedDotBits = 0;
      for (
        let dotRow = 0;
        dotRow < glyphGridGeometry.dotRowsPerCell;
        dotRow += 1
      ) {
        for (
          let dotColumn = 0;
          dotColumn < glyphGridGeometry.dotColumnsPerCell;
          dotColumn += 1
        ) {
          const sampleX =
            characterColumn * glyphGridGeometry.dotColumnsPerCell + dotColumn;
          const sampleY =
            characterRow * glyphGridGeometry.dotRowsPerCell + dotRow;
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
              glyphGrid.dotColumns,
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
        const glyphGrid = glyphGridGeometry.resolveGlyphGrid(
          displayContext,
          canvasElement,
          appearance.characterRows,
          appearance.glyphFontFamily,
        );
        if (
          samplingCanvas.width !== glyphGrid.dotColumns ||
          samplingCanvas.height !== glyphGrid.dotRows
        ) {
          samplingCanvas.width = glyphGrid.dotColumns;
          samplingCanvas.height = glyphGrid.dotRows;
        }
        glyphGridGeometry.drawSourceIntoDotGrid(
          samplingContext,
          imageSource,
          sourcePixelWidth,
          sourcePixelHeight,
          glyphGrid,
        );
        const dotPixels = samplingContext.getImageData(
          0,
          0,
          glyphGrid.dotColumns,
          glyphGrid.dotRows,
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
