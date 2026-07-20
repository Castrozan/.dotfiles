(function runAmbientCanvasPlayer() {
  const grid = document.getElementById("ambient-canvas-grid");
  const playlist = window.AMBIENT_CANVAS_PLAYLIST || [];
  const globalRotationSeconds = window.AMBIENT_CANVAS_ROTATION_SECONDS || 20;
  const sceneFactories = window.AMBIENT_CANVAS_SCENE_FACTORIES || {};

  if (!grid || playlist.length === 0) {
    return;
  }

  let currentDevicePixelRatio = window.devicePixelRatio || 1;

  function compositionDurationSeconds(composition) {
    return composition.durationSeconds || globalRotationSeconds;
  }

  const segmentBoundaries = [];
  let accumulatedCycleSeconds = 0;
  for (const composition of playlist) {
    const durationSeconds = compositionDurationSeconds(composition);
    segmentBoundaries.push({
      startSeconds: accumulatedCycleSeconds,
      durationSeconds: durationSeconds,
    });
    accumulatedCycleSeconds += durationSeconds;
  }
  const totalCycleSeconds = accumulatedCycleSeconds;

  function resolveSegment(elapsedSeconds) {
    const wrappedElapsedSeconds =
      ((elapsedSeconds % totalCycleSeconds) + totalCycleSeconds) %
      totalCycleSeconds;
    let precedingSeconds = 0;
    for (let index = 0; index < playlist.length; index += 1) {
      const durationSeconds = compositionDurationSeconds(playlist[index]);
      if (wrappedElapsedSeconds < precedingSeconds + durationSeconds) {
        return {
          index: index,
          localElapsedSeconds: wrappedElapsedSeconds - precedingSeconds,
        };
      }
      precedingSeconds += durationSeconds;
    }
    const lastIndex = playlist.length - 1;
    return {
      index: lastIndex,
      localElapsedSeconds: compositionDurationSeconds(playlist[lastIndex]),
    };
  }

  function applyLayout(compositionIndex) {
    const layout = playlist[compositionIndex].layout;
    if (!layout) {
      grid.style.gridTemplateColumns = "1fr";
      grid.style.gridTemplateRows = "1fr";
      grid.style.gridTemplateAreas = "";
      return;
    }
    grid.style.gridTemplateColumns = layout.columnTemplate;
    grid.style.gridTemplateRows = layout.rowTemplate;
    grid.style.gridTemplateAreas = layout.areaRows
      .map(function quoteAreaRow(areaRow) {
        return '"' + areaRow + '"';
      })
      .join(" ");
  }

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

  function buildSegment(compositionIndex) {
    const renderers = [];
    for (const paneConfiguration of playlist[compositionIndex].panes) {
      const sceneFactory = sceneFactories[paneConfiguration.scene];
      if (!sceneFactory) {
        console.error(
          "ambient-canvas: unknown scene " + paneConfiguration.scene,
        );
        continue;
      }
      const canvasElement = document.createElement("canvas");
      canvasElement.className = "ambient-canvas-pane";
      if (paneConfiguration.area) {
        canvasElement.style.gridArea = paneConfiguration.area;
      }
      grid.appendChild(canvasElement);
      sizeCanvasToPane(canvasElement);
      const rendererOptions = Object.assign(
        { devicePixelRatio: currentDevicePixelRatio },
        paneConfiguration.options || {},
        window.AMBIENT_CANVAS_RENDERER_OPTION_OVERRIDES || {},
      );
      try {
        renderers.push({
          canvasElement: canvasElement,
          renderer: sceneFactory(canvasElement, rendererOptions),
        });
      } catch (sceneInitializationError) {
        grid.removeChild(canvasElement);
        console.error(
          "ambient-canvas: scene " +
            paneConfiguration.scene +
            " failed to initialize: " +
            sceneInitializationError,
        );
      }
    }
    return { renderers: renderers, compositionIndex: compositionIndex };
  }

  function destroySegment(segmentHandle) {
    if (!segmentHandle) {
      return;
    }
    for (const activeRenderer of segmentHandle.renderers) {
      if (activeRenderer.renderer.dispose) {
        activeRenderer.renderer.dispose();
      }
      if (activeRenderer.canvasElement.parentNode === grid) {
        grid.removeChild(activeRenderer.canvasElement);
      }
    }
  }

  if (window.AMBIENT_CANVAS_RECORD_DRIVER) {
    window.AMBIENT_CANVAS_RECORD_DRIVER({
      totalCycleSeconds: totalCycleSeconds,
      segmentBoundaries: segmentBoundaries,
      resolveSegment: resolveSegment,
      applyLayout: applyLayout,
      buildSegment: buildSegment,
      destroySegment: destroySegment,
    });
    return;
  }

  let activeSegmentHandle = null;
  let activeSegmentIndex = null;

  function activateSegment(compositionIndex) {
    destroySegment(activeSegmentHandle);
    applyLayout(compositionIndex);
    activeSegmentHandle = buildSegment(compositionIndex);
    activeSegmentIndex = compositionIndex;
  }

  function handleWindowResize() {
    currentDevicePixelRatio = window.devicePixelRatio || 1;
    if (!activeSegmentHandle) {
      return;
    }
    for (const activeRenderer of activeSegmentHandle.renderers) {
      sizeCanvasToPane(activeRenderer.canvasElement);
      activeRenderer.renderer.resize(
        activeRenderer.canvasElement.width,
        activeRenderer.canvasElement.height,
      );
    }
  }

  let startTimestampMilliseconds = null;
  function renderFrame(timestampMilliseconds) {
    if (startTimestampMilliseconds === null) {
      startTimestampMilliseconds = timestampMilliseconds;
    }
    const elapsedSeconds =
      (timestampMilliseconds - startTimestampMilliseconds) / 1000.0;
    const segment = resolveSegment(elapsedSeconds);
    if (segment.index !== activeSegmentIndex) {
      activateSegment(segment.index);
    }
    for (const activeRenderer of activeSegmentHandle.renderers) {
      activeRenderer.renderer.render(segment.localElapsedSeconds);
    }
    window.requestAnimationFrame(renderFrame);
  }

  window.addEventListener("resize", handleWindowResize);
  window.requestAnimationFrame(renderFrame);
})();
