window.AmbientCanvasSixteenSegmentField = (function buildSixteenSegmentField() {
  const INTENSITY_LEVEL_COUNT = 32;
  const LIT_THRESHOLD = 0.17;
  const GAIN_MEDIAN = 0.73;
  const GAIN_SWING = 0.27;
  const GAIN_RADIANS_PER_SECOND = 0.21;
  const RED_LUMINANCE_WEIGHT = 0.2126;
  const GREEN_LUMINANCE_WEIGHT = 0.7152;
  const BLUE_LUMINANCE_WEIGHT = 0.0722;

  function resolveDisplayGain(elapsedSeconds) {
    return (
      GAIN_MEDIAN +
      GAIN_SWING * Math.sin(elapsedSeconds * GAIN_RADIANS_PER_SECOND)
    );
  }

  function resolveSegmentIntensity(
    fieldX,
    fieldY,
    segmentAngle,
    elapsedSeconds,
    displayGain,
  ) {
    const interference =
      Math.sin(fieldX * 4.1 + elapsedSeconds * 0.62) +
      Math.sin(fieldY * 5.7 - elapsedSeconds * 0.44) +
      Math.sin((fieldX + fieldY) * 3.3 + elapsedSeconds * 0.81) +
      Math.sin(
        Math.hypot(fieldX - 0.5, fieldY - 0.5) * 11.0 - elapsedSeconds * 1.15,
      );
    const positional = 0.5 + interference * 0.125;
    const flowAngle =
      Math.PI *
      (Math.sin(fieldX * 2.6 - elapsedSeconds * 0.37) +
        Math.cos(fieldY * 3.1 + elapsedSeconds * 0.29));
    const alignment = Math.abs(Math.cos(segmentAngle - flowAngle));
    const excited =
      Math.pow(positional, 2.0) * Math.pow(alignment, 3.0) * displayGain;
    if (excited <= LIT_THRESHOLD) {
      return 0;
    }
    return (excited - LIT_THRESHOLD) / (1 - LIT_THRESHOLD);
  }

  function buildLitFillStyles(alphaScale) {
    const fillStyles = new Array(INTENSITY_LEVEL_COUNT);
    for (let level = 0; level < INTENSITY_LEVEL_COUNT; level += 1) {
      const intensity = (level + 1) / INTENSITY_LEVEL_COUNT;
      const greenChannel = Math.round(88 + 132 * Math.pow(intensity, 0.7));
      const blueChannel = Math.round(8 + 148 * Math.pow(intensity, 2.4));
      const monochromeChannel = resolveMonochromeChannel(
        255,
        greenChannel,
        blueChannel,
      );
      const alpha = Math.min(1, (0.5 + 0.5 * intensity) * alphaScale);
      fillStyles[level] =
        "rgba(" +
        monochromeChannel +
        ", " +
        monochromeChannel +
        ", " +
        monochromeChannel +
        ", " +
        alpha.toFixed(3) +
        ")";
    }
    return fillStyles;
  }

  function resolveIntensityLevel(intensity) {
    const level = Math.floor(intensity * INTENSITY_LEVEL_COUNT);
    return level >= INTENSITY_LEVEL_COUNT ? INTENSITY_LEVEL_COUNT - 1 : level;
  }

  function resolveMonochromeChannel(redChannel, greenChannel, blueChannel) {
    return Math.round(
      redChannel * RED_LUMINANCE_WEIGHT +
        greenChannel * GREEN_LUMINANCE_WEIGHT +
        blueChannel * BLUE_LUMINANCE_WEIGHT,
    );
  }

  return {
    resolveDisplayGain,
    resolveSegmentIntensity,
    buildLitFillStyles,
    resolveIntensityLevel,
    resolveMonochromeChannel,
  };
})();
