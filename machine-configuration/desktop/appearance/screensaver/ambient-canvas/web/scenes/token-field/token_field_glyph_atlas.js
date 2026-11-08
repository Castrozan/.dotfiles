const tokenFieldFontFamilyStack =
  '"JetBrainsMono Nerd Font", "JetBrains Mono", Menlo, monospace';
const tokenFieldWhiteChannels = [255, 255, 255];
const tokenFieldHighlightWhiteShare = 0.18;
const tokenFieldIdentifierWhiteShare = 0.86;
const tokenFieldLiteralBackgroundShare = 0.32;
const tokenFieldOperatorBackgroundShare = 0.42;
const tokenFieldNoiseBackgroundShare = 0.34;

function tokenFieldMixChannels(from, to, toShare) {
  return from.map((channel, index) =>
    Math.round(channel + (to[index] - channel) * toShare),
  );
}

function tokenFieldBackgroundHueAtFullBrightness(backgroundChannels) {
  const brightest = Math.max(...backgroundChannels, 1);
  return backgroundChannels.map((channel) => (channel / brightest) * 255);
}

function tokenFieldResolveSyntaxColours(palette) {
  const background = palette.backgroundGlColor.map((channel) => channel * 255);
  const highlight = tokenFieldMixChannels(
    tokenFieldBackgroundHueAtFullBrightness(background),
    tokenFieldWhiteChannels,
    tokenFieldHighlightWhiteShare,
  );
  return {
    function: highlight,
    keyword: palette.accentOrangeColorChannels.split(",").map(Number),
    identifier: tokenFieldMixChannels(
      background,
      tokenFieldWhiteChannels,
      tokenFieldIdentifierWhiteShare,
    ),
    literal: tokenFieldMixChannels(
      highlight,
      background,
      tokenFieldLiteralBackgroundShare,
    ),
    operator: tokenFieldMixChannels(
      highlight,
      background,
      tokenFieldOperatorBackgroundShare,
    ),
    noise: tokenFieldMixChannels(
      highlight,
      background,
      tokenFieldNoiseBackgroundShare,
    ),
  };
}

function tokenFieldDrawGlyphRow(context, glyphs, cell, rowIndex) {
  for (let glyphIndex = 0; glyphIndex < glyphs.length; glyphIndex += 1) {
    context.fillText(
      glyphs[glyphIndex],
      glyphIndex * cell.width,
      rowIndex * cell.height + cell.height / 2,
    );
  }
}

function tokenFieldMeasureGlyphCell(fontSizePixels, rowHeightPixels) {
  const probe = document.createElement("canvas").getContext("2d");
  probe.font = `${fontSizePixels}px ${tokenFieldFontFamilyStack}`;
  return {
    width: Math.ceil(probe.measureText("M").width),
    height: rowHeightPixels,
  };
}

function tokenFieldBuildGlyphAtlas(atlasRequest) {
  const { palette, vocabulary, glyphs, fontSizePixels, cell } = atlasRequest;
  const colours = tokenFieldResolveSyntaxColours(palette);
  const colourRows = [...vocabulary.syntaxClasses, "noise"];
  const atlas = document.createElement("canvas");
  atlas.width = glyphs.length * cell.width;
  atlas.height = colourRows.length * cell.height;
  const context = atlas.getContext("2d");
  context.font = `${fontSizePixels}px ${tokenFieldFontFamilyStack}`;
  context.textBaseline = "middle";
  colourRows.forEach((syntaxClass, rowIndex) => {
    context.fillStyle = `rgb(${colours[syntaxClass].join(", ")})`;
    tokenFieldDrawGlyphRow(context, glyphs, cell, rowIndex);
  });
  return { atlas, noiseRowIndex: colourRows.length - 1 };
}

window.AmbientCanvasTokenFieldGlyphAtlas = {
  measureGlyphCell: tokenFieldMeasureGlyphCell,
  buildGlyphAtlas: tokenFieldBuildGlyphAtlas,
};
