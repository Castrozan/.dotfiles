window.AmbientCanvasTokenFieldGlyphAtlas =
  (function buildTokenFieldGlyphAtlas() {
    const FONT_FAMILY_STACK =
      '"JetBrainsMono Nerd Font", "JetBrains Mono", Menlo, monospace';
    const WHITE_CHANNELS = [255, 255, 255];
    const HIGHLIGHT_WHITE_SHARE = 0.18;
    const IDENTIFIER_WHITE_SHARE = 0.86;
    const LITERAL_BACKGROUND_SHARE = 0.32;
    const OPERATOR_BACKGROUND_SHARE = 0.42;
    const NOISE_BACKGROUND_SHARE = 0.34;

    function mixChannels(from, to, toShare) {
      return from.map((channel, index) =>
        Math.round(channel + (to[index] - channel) * toShare),
      );
    }

    function backgroundHueAtFullBrightness(backgroundChannels) {
      const brightest = Math.max(...backgroundChannels, 1);
      return backgroundChannels.map((channel) => (channel / brightest) * 255);
    }

    function resolveSyntaxColours(palette) {
      const background = palette.backgroundGlColor.map(
        (channel) => channel * 255,
      );
      const orange = palette.accentOrangeColorChannels.split(",").map(Number);
      const highlight = mixChannels(
        backgroundHueAtFullBrightness(background),
        WHITE_CHANNELS,
        HIGHLIGHT_WHITE_SHARE,
      );
      return {
        function: highlight,
        keyword: orange,
        identifier: mixChannels(
          background,
          WHITE_CHANNELS,
          IDENTIFIER_WHITE_SHARE,
        ),
        literal: mixChannels(highlight, background, LITERAL_BACKGROUND_SHARE),
        operator: mixChannels(highlight, background, OPERATOR_BACKGROUND_SHARE),
        noise: mixChannels(highlight, background, NOISE_BACKGROUND_SHARE),
      };
    }

    function drawGlyphRow(context, glyphs, cell, rowIndex) {
      for (let glyphIndex = 0; glyphIndex < glyphs.length; glyphIndex += 1) {
        context.fillText(
          glyphs[glyphIndex],
          glyphIndex * cell.width,
          rowIndex * cell.height + cell.height / 2,
        );
      }
    }

    function measureGlyphCell(fontSizePixels, rowHeightPixels) {
      const probe = document.createElement("canvas").getContext("2d");
      probe.font = `${fontSizePixels}px ${FONT_FAMILY_STACK}`;
      return {
        width: Math.ceil(probe.measureText("M").width),
        height: rowHeightPixels,
      };
    }

    function buildGlyphAtlas(
      palette,
      vocabulary,
      glyphs,
      fontSizePixels,
      cell,
    ) {
      const colours = resolveSyntaxColours(palette);
      const colourRows = [...vocabulary.syntaxClasses, "noise"];
      const atlas = document.createElement("canvas");
      atlas.width = glyphs.length * cell.width;
      atlas.height = colourRows.length * cell.height;
      const context = atlas.getContext("2d");
      context.font = `${fontSizePixels}px ${FONT_FAMILY_STACK}`;
      context.textBaseline = "middle";
      colourRows.forEach((syntaxClass, rowIndex) => {
        context.fillStyle = `rgb(${colours[syntaxClass].join(", ")})`;
        drawGlyphRow(context, glyphs, cell, rowIndex);
      });
      return { atlas, noiseRowIndex: colourRows.length - 1 };
    }

    return { measureGlyphCell, buildGlyphAtlas };
  })();
