(function registerBadAppleScene() {
  const VIDEO_DIRECTORY_URL = "ambient-canvas-videos";
  const DEFAULT_CHARACTER_ROWS = 64;
  const DEFAULT_LUMINANCE_THRESHOLD = 0.45;
  const DEFAULT_GLYPH_COLOR = "#c8e6ff";
  const DEFAULT_GLYPH_FONT_FAMILY = "Menlo, monospace";
  const BACKGROUND_FILL_STYLE = "#0a1a2f";

  function resolveAppearance(options) {
    return {
      characterRows:
        (options && options.characterRows) || DEFAULT_CHARACTER_ROWS,
      luminanceThreshold:
        (options && options.luminanceThreshold) || DEFAULT_LUMINANCE_THRESHOLD,
      glyphColor: (options && options.glyphColor) || DEFAULT_GLYPH_COLOR,
      glyphFontFamily:
        (options && options.glyphFontFamily) || DEFAULT_GLYPH_FONT_FAMILY,
      backgroundFillStyle: BACKGROUND_FILL_STYLE,
    };
  }

  function createBadAppleRenderer(canvasElement, options) {
    const renderBrailleFrame =
      window.AmbientCanvasBrailleFrameRenderer.createBrailleFrameRenderer(
        canvasElement,
        resolveAppearance(options),
      );
    const videoSource =
      window.AmbientCanvasSeekableVideoSource.createSeekableVideoSource(
        VIDEO_DIRECTORY_URL + "/" + options.videoId + ".mp4",
        (options && options.startSeconds) || 0,
        Boolean(options && options.deterministicPlayback),
      );

    return {
      ready: videoSource.ready,
      prepareFrame(localElapsedSeconds) {
        return videoSource.prepareFrame(localElapsedSeconds);
      },
      render() {
        renderBrailleFrame(
          videoSource.element,
          videoSource.element.videoWidth,
          videoSource.element.videoHeight,
        );
      },
      resize() {},
      dispose() {
        videoSource.dispose();
      },
    };
  }

  window.AMBIENT_CANVAS_SCENE_FACTORIES =
    window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  window.AMBIENT_CANVAS_SCENE_FACTORIES["bad-apple"] = createBadAppleRenderer;
})();
