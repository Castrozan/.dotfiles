(function runAmbientCanvasPlayer() {
  const grid = document.getElementById("ambient-canvas-grid");
  const paneConfigurations = window.AMBIENT_CANVAS_PANES || [];
  const sceneFactories = window.AMBIENT_CANVAS_SCENE_FACTORIES || {};

  if (!grid || paneConfigurations.length === 0) {
    return;
  }

  const columnCount = Math.ceil(Math.sqrt(paneConfigurations.length));
  const rowCount = Math.ceil(paneConfigurations.length / columnCount);
  grid.style.gridTemplateColumns = "repeat(" + columnCount + ", 1fr)";
  grid.style.gridTemplateRows = "repeat(" + rowCount + ", 1fr)";

  let currentDevicePixelRatio = window.devicePixelRatio || 1;

  function sizeCanvasToPane(canvasElement) {
    const bounds = canvasElement.getBoundingClientRect();
    canvasElement.width = Math.max(
      1,
      Math.floor(bounds.width * currentDevicePixelRatio),
    );
    canvasElement.height = Math.max(
      1,
      Math.floor(bounds.height * currentDevicePixelRatio),
    );
  }

  const activeRenderers = [];
  for (const paneConfiguration of paneConfigurations) {
    const sceneFactory = sceneFactories[paneConfiguration.scene];
    if (!sceneFactory) {
      console.error("ambient-canvas: unknown scene " + paneConfiguration.scene);
      continue;
    }
    const canvasElement = document.createElement("canvas");
    canvasElement.className = "ambient-canvas-pane";
    grid.appendChild(canvasElement);
    sizeCanvasToPane(canvasElement);
    const rendererOptions = Object.assign(
      { devicePixelRatio: currentDevicePixelRatio },
      paneConfiguration.options || {},
    );
    try {
      activeRenderers.push({
        canvasElement: canvasElement,
        renderer: sceneFactory(canvasElement, rendererOptions),
      });
    } catch (sceneInitializationError) {
      console.error(
        "ambient-canvas: scene " +
          paneConfiguration.scene +
          " failed to initialize: " +
          sceneInitializationError,
      );
    }
  }

  function handleWindowResize() {
    currentDevicePixelRatio = window.devicePixelRatio || 1;
    for (const activeRenderer of activeRenderers) {
      sizeCanvasToPane(activeRenderer.canvasElement);
      activeRenderer.renderer.resize(
        activeRenderer.canvasElement.width,
        activeRenderer.canvasElement.height,
      );
    }
  }
  window.addEventListener("resize", handleWindowResize);

  let startTimestampMilliseconds = null;
  function renderFrame(timestampMilliseconds) {
    if (startTimestampMilliseconds === null) {
      startTimestampMilliseconds = timestampMilliseconds;
    }
    const elapsedSeconds =
      (timestampMilliseconds - startTimestampMilliseconds) / 1000.0;
    for (const activeRenderer of activeRenderers) {
      activeRenderer.renderer.render(elapsedSeconds);
    }
    window.requestAnimationFrame(renderFrame);
  }
  window.requestAnimationFrame(renderFrame);
})();
