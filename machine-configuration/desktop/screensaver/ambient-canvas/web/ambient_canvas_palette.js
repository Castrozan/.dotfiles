window.AmbientCanvasPalette = (function buildAmbientCanvasPalette() {
  const BACKGROUND_HEX = "#0a1a2f";
  const ACCENT_ORANGE_HEX = "#ff6c18";
  const LUMINANCE_SAMPLING_FLOOR_HEX = "#000000";

  function colorChannelsFromHex(hexColor) {
    return [
      parseInt(hexColor.slice(1, 3), 16),
      parseInt(hexColor.slice(3, 5), 16),
      parseInt(hexColor.slice(5, 7), 16),
    ];
  }

  function joinedColorChannels(colorChannels) {
    return colorChannels.join(", ");
  }

  function normalizedColorChannels(colorChannels) {
    return colorChannels.map(function normalizeOneChannel(channelValue) {
      return channelValue / 255;
    });
  }

  function glslVectorLiteral(normalizedChannels) {
    const formattedChannels = normalizedChannels.map(
      function formatOneChannel(channelValue) {
        return channelValue.toFixed(6);
      },
    );
    return "vec3(" + formattedChannels.join(", ") + ")";
  }

  const backgroundColorChannels = colorChannelsFromHex(BACKGROUND_HEX);
  const backgroundGlColor = normalizedColorChannels(backgroundColorChannels);

  return {
    backgroundHex: BACKGROUND_HEX,
    backgroundColorChannels: joinedColorChannels(backgroundColorChannels),
    backgroundGlColor: backgroundGlColor,
    backgroundGlslVector: glslVectorLiteral(backgroundGlColor),
    accentOrangeColorChannels: joinedColorChannels(
      colorChannelsFromHex(ACCENT_ORANGE_HEX),
    ),
    luminanceSamplingFloorHex: LUMINANCE_SAMPLING_FLOOR_HEX,
  };
})();
