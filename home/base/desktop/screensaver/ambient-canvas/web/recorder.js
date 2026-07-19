(function installAmbientCanvasDeterministicRecorder() {
  const recordParameters = new URLSearchParams(window.location.search);
  if (!recordParameters.has("record")) {
    return;
  }

  const captureDurationSeconds = Number(recordParameters.get("seconds")) || 30;
  const captureFramesPerSecond = Number(recordParameters.get("fps")) || 30;
  const uploadUrl = recordParameters.get("uploadUrl") || "";

  const outputPixelWidth = 1920;
  const outputPixelHeight = 1080;
  const targetBitsPerPixelPerFrame = 0.35;
  const keyFrameIntervalSeconds = 2;
  const encoderQueueHighWatermark = 8;
  const encoderQueueDrainTarget = 4;

  window.AMBIENT_CANVAS_RENDERER_OPTION_OVERRIDES = {
    preserveDrawingBuffer: true,
  };

  function nextAnimationFrame() {
    return new Promise(function resolveOnNextFrame(resolve) {
      window.requestAnimationFrame(function frameArrived() {
        resolve();
      });
    });
  }

  function waitForEncoderQueueToDrain(videoEncoder) {
    return new Promise(function resolveWhenDrained(resolve) {
      function checkQueueDepth() {
        if (videoEncoder.encodeQueueSize <= encoderQueueDrainTarget) {
          resolve();
          return;
        }
        window.setTimeout(checkQueueDepth, 4);
      }
      checkQueueDepth();
    });
  }

  function forceDeterministicGridLayout() {
    const grid = document.getElementById("ambient-canvas-grid");
    grid.style.position = "fixed";
    grid.style.left = "0";
    grid.style.top = "0";
    grid.style.width = outputPixelWidth + "px";
    grid.style.height = outputPixelHeight + "px";
    return grid;
  }

  function resolveFixedResolutionPanePlacements(activeRenderers, grid) {
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

  function createRecordCanvasContext() {
    const recordCanvas = document.createElement("canvas");
    recordCanvas.width = outputPixelWidth;
    recordCanvas.height = outputPixelHeight;
    return recordCanvas.getContext("2d");
  }

  function renderFixedResolutionFrame(
    recordContext,
    panePlacements,
    elapsedSeconds,
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

  function createConfiguredMuxerAndEncoder() {
    const muxer = new Mp4Muxer.Muxer({
      target: new Mp4Muxer.ArrayBufferTarget(),
      video: {
        codec: "avc",
        width: outputPixelWidth,
        height: outputPixelHeight,
      },
      fastStart: "in-memory",
    });
    const videoEncoder = new VideoEncoder({
      output: function muxEncodedChunk(encodedChunk, chunkMetadata) {
        muxer.addVideoChunk(encodedChunk, chunkMetadata);
      },
      error: function reportEncodeError(encodeError) {
        console.error("ambient-canvas record: encode error", encodeError);
      },
    });
    videoEncoder.configure({
      codec: "avc1.640028",
      width: outputPixelWidth,
      height: outputPixelHeight,
      bitrate: Math.round(
        outputPixelWidth *
          outputPixelHeight *
          captureFramesPerSecond *
          targetBitsPerPixelPerFrame,
      ),
      framerate: captureFramesPerSecond,
    });
    return { muxer, videoEncoder };
  }

  function uploadEncodedLoop(encodedBuffer) {
    if (!uploadUrl) {
      return Promise.resolve();
    }
    return fetch(uploadUrl + "?extension=mp4", {
      method: "POST",
      body: new Blob([encodedBuffer], { type: "video/mp4" }),
    })
      .catch(function ignoreUploadFailure() {})
      .finally(function closeAfterUpload() {
        window.setTimeout(function requestWindowClose() {
          window.close();
        }, 250);
      });
  }

  async function driveDeterministicRecording(activeRenderers) {
    const grid = forceDeterministicGridLayout();
    await nextAnimationFrame();
    const panePlacements = resolveFixedResolutionPanePlacements(
      activeRenderers,
      grid,
    );
    const recordContext = createRecordCanvasContext();
    const { muxer, videoEncoder } = createConfiguredMuxerAndEncoder();

    const totalFrameCount = Math.round(
      captureDurationSeconds * captureFramesPerSecond,
    );
    const microsecondsPerFrame = 1000000 / captureFramesPerSecond;
    const keyFrameIntervalFrames = Math.round(
      keyFrameIntervalSeconds * captureFramesPerSecond,
    );

    for (let frameIndex = 0; frameIndex < totalFrameCount; frameIndex++) {
      const elapsedSeconds = frameIndex / captureFramesPerSecond;
      renderFixedResolutionFrame(recordContext, panePlacements, elapsedSeconds);
      const videoFrame = new VideoFrame(recordContext.canvas, {
        timestamp: Math.round(frameIndex * microsecondsPerFrame),
        duration: Math.round(microsecondsPerFrame),
      });
      videoEncoder.encode(videoFrame, {
        keyFrame: frameIndex % keyFrameIntervalFrames === 0,
      });
      videoFrame.close();
      if (videoEncoder.encodeQueueSize > encoderQueueHighWatermark) {
        await waitForEncoderQueueToDrain(videoEncoder);
      }
    }

    await videoEncoder.flush();
    muxer.finalize();
    await uploadEncodedLoop(muxer.target.buffer);
  }

  window.AMBIENT_CANVAS_RECORD_DRIVER = function startDeterministicRecording(
    activeRenderers,
  ) {
    driveDeterministicRecording(activeRenderers).catch(
      function reportRecordingFailure(recordingError) {
        console.error("ambient-canvas record: driver failed", recordingError);
      },
    );
  };
})();
