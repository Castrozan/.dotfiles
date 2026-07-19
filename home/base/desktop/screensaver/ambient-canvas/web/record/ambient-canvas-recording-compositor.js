window.AmbientCanvasRecordingCompositor = (function buildCompositor() {
  function forceDeterministicGridLayout(outputPixelWidth, outputPixelHeight) {
    const grid = document.getElementById("ambient-canvas-grid");
    grid.style.position = "fixed";
    grid.style.left = "0";
    grid.style.top = "0";
    grid.style.width = outputPixelWidth + "px";
    grid.style.height = outputPixelHeight + "px";
    return grid;
  }

  function resolveFixedResolutionPanePlacements(
    activeRenderers,
    grid,
    outputPixelWidth,
    outputPixelHeight,
  ) {
    const gridBounds = grid.getBoundingClientRect();
    const horizontalScale = outputPixelWidth / gridBounds.width;
    const verticalScale = outputPixelHeight / gridBounds.height;
    const panePlacements = [];
    for (const activeRenderer of activeRenderers) {
      const bounds = activeRenderer.canvasElement.getBoundingClientRect();
      const panedPixelWidth = Math.max(
        1,
        Math.round(bounds.width * horizontalScale),
      );
      const panedPixelHeight = Math.max(
        1,
        Math.round(bounds.height * verticalScale),
      );
      activeRenderer.canvasElement.width = panedPixelWidth;
      activeRenderer.canvasElement.height = panedPixelHeight;
      activeRenderer.renderer.resize(panedPixelWidth, panedPixelHeight);
      panePlacements.push({
        renderer: activeRenderer.renderer,
        canvasElement: activeRenderer.canvasElement,
        destinationLeft: Math.round(
          (bounds.left - gridBounds.left) * horizontalScale,
        ),
        destinationTop: Math.round(
          (bounds.top - gridBounds.top) * verticalScale,
        ),
        destinationWidth: panedPixelWidth,
        destinationHeight: panedPixelHeight,
      });
    }
    return panePlacements;
  }

  function createRecordCanvasContext(outputPixelWidth, outputPixelHeight) {
    const recordCanvas = document.createElement("canvas");
    recordCanvas.width = outputPixelWidth;
    recordCanvas.height = outputPixelHeight;
    return recordCanvas.getContext("2d");
  }

  function prepareFixedResolutionFrame(panePlacements, localElapsedSeconds) {
    return Promise.all(
      panePlacements.map(function prepareOnePane(panePlacement) {
        if (!panePlacement.renderer.prepareFrame) {
          return Promise.resolve();
        }
        return panePlacement.renderer.prepareFrame(localElapsedSeconds);
      }),
    );
  }

  function renderFixedResolutionFrame(
    recordContext,
    panePlacements,
    elapsedSeconds,
    outputPixelWidth,
    outputPixelHeight,
  ) {
    recordContext.fillStyle = "#0a1a2f";
    recordContext.fillRect(0, 0, outputPixelWidth, outputPixelHeight);
    for (const panePlacement of panePlacements) {
      panePlacement.renderer.render(elapsedSeconds);
      recordContext.drawImage(
        panePlacement.canvasElement,
        panePlacement.destinationLeft,
        panePlacement.destinationTop,
        panePlacement.destinationWidth,
        panePlacement.destinationHeight,
      );
    }
  }

  return {
    forceDeterministicGridLayout,
    resolveFixedResolutionPanePlacements,
    createRecordCanvasContext,
    prepareFixedResolutionFrame,
    renderFixedResolutionFrame,
  };
})();
