window.AmbientCanvasAsciiInvaderGlyphField =
  (function buildAsciiInvaderGlyphField() {
    const shell = window.AmbientCanvasAsciiInvaderShell;
    const VIEWER_DISTANCE = 3.15;
    const PROJECTION_FOCAL_LENGTH = 1.05;
    const SHELL_SCREEN_FRACTION = 1.15;
    const BASE_GLYPH_FRACTION = 0.04;
    const MONOSPACE_ADVANCE_RATIO = 0.6;
    const STAR_COUNT = 150;
    const STATUS_DOT_COUNT = 9;
    const CRT_SCREEN_FIELD_HEX = window.AmbientCanvasPalette.backgroundHex;

    function paintScreenField(context, width, height) {
      context.fillStyle = CRT_SCREEN_FIELD_HEX;
      context.fillRect(0, 0, width, height);
    }

    function paintStars(context, width, height, elapsedSeconds) {
      for (let starIndex = 0; starIndex < STAR_COUNT; starIndex += 1) {
        const horizontal = shell.hashedUnitInterval(starIndex, 19.0) * width;
        const vertical = shell.hashedUnitInterval(starIndex, 23.0) * height;
        const twinkle =
          0.55 +
          0.45 *
            Math.sin(
              elapsedSeconds * 1.7 +
                shell.hashedUnitInterval(starIndex, 29.0) * 6.28,
            );
        const palette =
          shell.hashedUnitInterval(starIndex, 31.0) < 0.62
            ? [1.0, 1.0, 1.0]
            : shell.PHOSPHOR_PALETTE[
                Math.floor(
                  shell.hashedUnitInterval(starIndex, 37.0) *
                    shell.PHOSPHOR_PALETTE.length,
                )
              ];
        const size = Math.max(1, Math.round(height * 0.0042));
        context.fillStyle = colourWithAlpha(palette, 0.3 + 0.55 * twinkle);
        context.fillRect(horizontal, vertical, size, size);
      }
    }

    function paintStatusDots(context, width, height) {
      const dotSize = Math.max(1, Math.round(height * 0.0055));
      const startHorizontal = width * 0.055;
      const vertical = height * 0.935;
      context.fillStyle = "rgba(235, 235, 235, 0.78)";
      for (let dotIndex = 0; dotIndex < STATUS_DOT_COUNT; dotIndex += 1) {
        const spacing =
          width * (0.019 + 0.006 * shell.hashedUnitInterval(dotIndex, 41.0));
        context.fillRect(
          startHorizontal + dotIndex * spacing,
          vertical,
          dotSize,
          dotSize,
        );
      }
    }

    function colourWithAlpha(palette, alpha) {
      const red = Math.round(palette[0] * 255);
      const green = Math.round(palette[1] * 255);
      const blue = Math.round(palette[2] * 255);
      return "rgba(" + red + "," + green + "," + blue + "," + alpha + ")";
    }

    function paintShell(context, width, height, elapsedSeconds, shellPoints) {
      const centreHorizontal = width * 0.5;
      const centreVertical = height * 0.5;
      const screenScale = Math.min(width, height) * SHELL_SCREEN_FRACTION;
      const baseGlyphPixels = Math.min(width, height) * BASE_GLYPH_FRACTION;
      const projected = [];

      for (
        let pointIndex = 0;
        pointIndex < shellPoints.length;
        pointIndex += 1
      ) {
        const point = shellPoints[pointIndex];
        const [tumbledX, tumbledY, tumbledZ] = shell.tumbledPosition(
          point.restingPosition,
          elapsedSeconds,
        );
        const depth = VIEWER_DISTANCE + tumbledZ;
        if (depth <= 0.25) {
          continue;
        }
        const perspective = PROJECTION_FOCAL_LENGTH / depth;
        const cellWidth = baseGlyphPixels * MONOSPACE_ADVANCE_RATIO;
        projected.push({
          point,
          depth,
          cellColumn: Math.round(
            (centreHorizontal + tumbledX * perspective * screenScale) /
              cellWidth,
          ),
          cellRow: Math.round(
            (centreVertical + tumbledY * perspective * screenScale) /
              baseGlyphPixels,
          ),
          facing: (VIEWER_DISTANCE - depth + 1.0) / 2.0,
        });
      }

      projected.sort((left, right) => left.depth - right.depth);

      const cellWidth = baseGlyphPixels * MONOSPACE_ADVANCE_RATIO;
      const occupiedCells = {};
      context.font = Math.max(6, Math.round(baseGlyphPixels)) + "px monospace";

      for (let drawIndex = 0; drawIndex < projected.length; drawIndex += 1) {
        const entry = projected[drawIndex];
        const cellKey = entry.cellColumn + "," + entry.cellRow;
        if (occupiedCells[cellKey]) {
          continue;
        }
        const flicker =
          0.82 +
          0.18 * Math.sin(elapsedSeconds * 4.1 + entry.point.flickerPhase);
        const presence = Math.max(0.0, Math.min(1.0, entry.facing)) * flicker;
        if (presence < 0.12) {
          continue;
        }
        occupiedCells[cellKey] = true;
        context.shadowColor = colourWithAlpha(entry.point.colour, 0.85);
        context.shadowBlur = baseGlyphPixels * 0.75 * presence;
        context.fillStyle = colourWithAlpha(
          entry.point.colour,
          0.35 + 0.65 * presence,
        );
        context.fillText(
          entry.point.glyph,
          entry.cellColumn * cellWidth,
          entry.cellRow * baseGlyphPixels,
        );
      }
      context.shadowBlur = 0;
    }

    function paintGlyphField(
      context,
      width,
      height,
      elapsedSeconds,
      shellPoints,
    ) {
      paintScreenField(context, width, height);
      context.textAlign = "center";
      context.textBaseline = "middle";
      paintStars(context, width, height, elapsedSeconds);
      paintShell(context, width, height, elapsedSeconds, shellPoints);
      paintStatusDots(context, width, height);
    }

    return { paintGlyphField };
  })();
