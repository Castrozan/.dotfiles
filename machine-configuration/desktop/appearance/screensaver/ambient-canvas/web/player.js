{
  const playerGrid = document.getElementById("ambient-canvas-grid");
  const playerPlaylist = window.AMBIENT_CANVAS_PLAYLIST || [];
  const playerGlobalRotationSeconds =
    window.AMBIENT_CANVAS_ROTATION_SECONDS || 20;
  const playerSceneFactories = window.AMBIENT_CANVAS_SCENE_FACTORIES || {};
  const playerState = {
    currentDevicePixelRatio: window.devicePixelRatio || 1,
    activeSegmentHandle: null,
    activeSegmentIndex: null,
    startTimestampMilliseconds: null,
  };

  const playerCompositionDurationSeconds = (composition) =>
    composition.durationSeconds || playerGlobalRotationSeconds;

  const playerTotalCycleSeconds = playerPlaylist.reduce(
    function accumulateCycleSeconds(precedingSeconds, composition) {
      return precedingSeconds + playerCompositionDurationSeconds(composition);
    },
    0,
  );

  const playerResolveSegment = (elapsedSeconds) => {
    const wrappedElapsedSeconds =
      ((elapsedSeconds % playerTotalCycleSeconds) + playerTotalCycleSeconds) %
      playerTotalCycleSeconds;
    let precedingSeconds = 0;
    for (let index = 0; index < playerPlaylist.length; index += 1) {
      const durationSeconds = playerCompositionDurationSeconds(
        playerPlaylist[index],
      );
      if (wrappedElapsedSeconds < precedingSeconds + durationSeconds) {
        return {
          index: index,
          localElapsedSeconds: wrappedElapsedSeconds - precedingSeconds,
        };
      }
      precedingSeconds += durationSeconds;
    }
    const lastIndex = playerPlaylist.length - 1;
    return {
      index: lastIndex,
      localElapsedSeconds: playerCompositionDurationSeconds(
        playerPlaylist[lastIndex],
      ),
    };
  };

  const playerApplyLayout = (compositionIndex) => {
    const layout = playerPlaylist[compositionIndex].layout;
    if (!layout) {
      playerGrid.style.gridTemplateColumns = "1fr";
      playerGrid.style.gridTemplateRows = "1fr";
      playerGrid.style.gridTemplateAreas = "";
      return;
    }
    playerGrid.style.gridTemplateColumns = layout.columnTemplate;
    playerGrid.style.gridTemplateRows = layout.rowTemplate;
    playerGrid.style.gridTemplateAreas = layout.areaRows
      .map(function quoteAreaRow(areaRow) {
        return '"' + areaRow + '"';
      })
      .join(" ");
  };

  const playerSizeCanvasToPane = (canvasElement) => {
    const bounds = canvasElement.getBoundingClientRect();
    canvasElement.width = Math.max(
      1,
      Math.floor(bounds.width * playerState.currentDevicePixelRatio),
    );
    canvasElement.height = Math.max(
      1,
      Math.floor(bounds.height * playerState.currentDevicePixelRatio),
    );
  };

  const playerBuildPaneRenderer = (
    paneConfiguration,
    sceneFactory,
    recordingOptionOverrides,
  ) => {
    const canvasElement = document.createElement("canvas");
    canvasElement.className = "ambient-canvas-pane";
    if (paneConfiguration.area) {
      canvasElement.style.gridArea = paneConfiguration.area;
    }
    playerGrid.appendChild(canvasElement);
    playerSizeCanvasToPane(canvasElement);
    const rendererOptions = Object.assign(
      { devicePixelRatio: playerState.currentDevicePixelRatio },
      paneConfiguration.options,
      window.AMBIENT_CANVAS_RENDERER_OPTION_OVERRIDES,
      recordingOptionOverrides,
    );
    try {
      return {
        canvasElement: canvasElement,
        renderer: sceneFactory(canvasElement, rendererOptions),
      };
    } catch (sceneInitializationError) {
      playerGrid.removeChild(canvasElement);
      console.error(
        "ambient-canvas: scene " +
          paneConfiguration.scene +
          " failed to initialize: " +
          sceneInitializationError,
      );
      return null;
    }
  };

  const playerBuildSegment = (compositionIndex, recordingOptionOverrides) => {
    const renderers = [];
    for (const paneConfiguration of playerPlaylist[compositionIndex].panes) {
      const sceneFactory = playerSceneFactories[paneConfiguration.scene];
      if (!sceneFactory) {
        console.error(
          "ambient-canvas: unknown scene " + paneConfiguration.scene,
        );
        continue;
      }
      const activeRenderer = playerBuildPaneRenderer(
        paneConfiguration,
        sceneFactory,
        recordingOptionOverrides,
      );
      if (activeRenderer) renderers.push(activeRenderer);
    }
    return { renderers: renderers, compositionIndex: compositionIndex };
  };

  const playerDestroySegment = (segmentHandle) => {
    if (!segmentHandle) {
      return;
    }
    for (const activeRenderer of segmentHandle.renderers) {
      if (activeRenderer.renderer.dispose) {
        activeRenderer.renderer.dispose();
      }
      if (activeRenderer.canvasElement.parentNode === playerGrid) {
        playerGrid.removeChild(activeRenderer.canvasElement);
      }
    }
  };

  const playerActivateSegment = (compositionIndex) => {
    playerDestroySegment(playerState.activeSegmentHandle);
    playerApplyLayout(compositionIndex);
    playerState.activeSegmentHandle = playerBuildSegment(compositionIndex);
    playerState.activeSegmentIndex = compositionIndex;
  };

  const playerHandleWindowResize = () => {
    playerState.currentDevicePixelRatio = window.devicePixelRatio || 1;
    if (!playerState.activeSegmentHandle) {
      return;
    }
    for (const activeRenderer of playerState.activeSegmentHandle.renderers) {
      playerSizeCanvasToPane(activeRenderer.canvasElement);
      activeRenderer.renderer.resize(
        activeRenderer.canvasElement.width,
        activeRenderer.canvasElement.height,
      );
    }
  };

  const playerRenderFrame = (timestampMilliseconds) => {
    if (playerState.startTimestampMilliseconds === null) {
      playerState.startTimestampMilliseconds = timestampMilliseconds;
    }
    const elapsedSeconds =
      (timestampMilliseconds - playerState.startTimestampMilliseconds) / 1000.0;
    const segment = playerResolveSegment(elapsedSeconds);
    if (segment.index !== playerState.activeSegmentIndex) {
      playerActivateSegment(segment.index);
    }
    for (const activeRenderer of playerState.activeSegmentHandle.renderers) {
      activeRenderer.renderer.render(segment.localElapsedSeconds);
    }
    window.requestAnimationFrame(playerRenderFrame);
  };

  if (playerGrid && playerPlaylist.length > 0) {
    if (window.AMBIENT_CANVAS_RECORD_DRIVER) {
      window.AMBIENT_CANVAS_RECORD_DRIVER({
        compositions: playerPlaylist,
        compositionDurationSeconds: playerCompositionDurationSeconds,
        applyLayout: playerApplyLayout,
        buildSegment: playerBuildSegment,
        destroySegment: playerDestroySegment,
      });
    } else {
      window.addEventListener("resize", playerHandleWindowResize);
      window.requestAnimationFrame(playerRenderFrame);
    }
  }
}
