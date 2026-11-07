const BRAILLE_FRAME_PATTERN_BASE_CODE_POINT = 0x2800;
const BRAILLE_FRAME_DOT_BIT_BY_ROW_AND_COLUMN = [
  [0x01, 0x08],
  [0x02, 0x10],
  [0x04, 0x20],
  [0x40, 0x80],
];

const brailleFrameGlyphGridGeometry = window.AmbientCanvasBrailleGlyphGrid;

function brailleFrameIsDotRaised(dotSampling, sampleX, sampleY) {
  const sampleOffset = (sampleY * dotSampling.dotColumns + sampleX) * 4;
  const luminance =
    (dotSampling.dotPixels[sampleOffset] * 0.2126 +
      dotSampling.dotPixels[sampleOffset + 1] * 0.7152 +
      dotSampling.dotPixels[sampleOffset + 2] * 0.0722) /
    255;
  return luminance >= dotSampling.luminanceThreshold;
}

function brailleFrameResolveRaisedDotBit(dotSampling, sampleX, sampleY, dotBit) {
  return brailleFrameIsDotRaised(dotSampling, sampleX, sampleY) ? dotBit : 0;
}

function brailleFrameResolveRaisedDotBitsInDotRow(
  dotSampling,
  characterRow,
  characterColumn,
  dotRow,
) {
  let raisedDotBits = 0;
  for (
    let dotColumn = 0;
    dotColumn < brailleFrameGlyphGridGeometry.dotColumnsPerCell;
    dotColumn += 1
  ) {
    const sampleX =
      characterColumn * brailleFrameGlyphGridGeometry.dotColumnsPerCell + dotColumn;
    const sampleY = characterRow * brailleFrameGlyphGridGeometry.dotRowsPerCell + dotRow;
    raisedDotBits |= brailleFrameResolveRaisedDotBit(
      dotSampling,
      sampleX,
      sampleY,
      BRAILLE_FRAME_DOT_BIT_BY_ROW_AND_COLUMN[dotRow][dotColumn],
    );
  }
  return raisedDotBits;
}

function brailleFrameResolveCellCodePoint(
  dotSampling,
  characterRow,
  characterColumn,
) {
  let raisedDotBits = 0;
  for (let dotRow = 0; dotRow < brailleFrameGlyphGridGeometry.dotRowsPerCell; dotRow += 1) {
    raisedDotBits |= brailleFrameResolveRaisedDotBitsInDotRow(
      dotSampling,
      characterRow,
      characterColumn,
      dotRow,
    );
  }
  return BRAILLE_FRAME_PATTERN_BASE_CODE_POINT + raisedDotBits;
}

function brailleFrameResolveGlyphRowText(dotSampling, glyphGrid, characterRow) {
  let glyphRowText = "";
  for (
    let characterColumn = 0;
    characterColumn < glyphGrid.characterColumns;
    characterColumn += 1
  ) {
    glyphRowText += String.fromCharCode(
      brailleFrameResolveCellCodePoint(dotSampling, characterRow, characterColumn),
    );
  }
  return glyphRowText;
}

function brailleFramePaintGlyphs(
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
  const dotSampling = {
    dotPixels,
    dotColumns: glyphGrid.dotColumns,
    luminanceThreshold: appearance.luminanceThreshold,
  };
  for (
    let characterRow = 0;
    characterRow < glyphGrid.characterRows;
    characterRow += 1
  ) {
    displayContext.fillText(
      brailleFrameResolveGlyphRowText(dotSampling, glyphGrid, characterRow),
      horizontalInset,
      characterRow * glyphGrid.fontSize,
    );
  }
}

window.AmbientCanvasBrailleFrameRenderer =
  (function buildBrailleFrameRenderer() {
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
        const glyphGrid = brailleFrameGlyphGridGeometry.resolveGlyphGrid(
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
        brailleFrameGlyphGridGeometry.drawSourceIntoDotGrid(
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
        brailleFramePaintGlyphs(
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
