(function installAmbientCanvasDeterministicRecorder() {
  const recordParameters = new URLSearchParams(window.location.search);
  if (!recordParameters.has("record")) {
    return;
  }

  const explicitCaptureDurationSeconds =
    Number(recordParameters.get("seconds")) || 0;
  const captureFramesPerSecond = Number(recordParameters.get("fps")) || 30;
  const uploadUrl = recordParameters.get("uploadUrl") || "";

  const outputPixelWidth = 1920;
  const outputPixelHeight = 1080;
  const targetBitsPerPixelPerFrame = 0.35;
  const keyFrameIntervalSeconds = 2;
  const encoderQueueHighWatermark = 8;
  const encoderQueueDrainTarget = 4;

  const compositor = window.AmbientCanvasRecordingCompositor;
  const encoder = window.AmbientCanvasRecordingEncoder;

  window.AMBIENT_CANVAS_RENDERER_OPTION_OVERRIDES = {
    preserveDrawingBuffer: true,
    deterministicPlayback: true,
  };

  function waitForSegmentAssetsToLoad(segmentHandle) {
    return Promise.all(
      segmentHandle.renderers.map(function awaitOneRenderer(activeRenderer) {
        return activeRenderer.renderer.ready || Promise.resolve();
      }),
    );
  }

  function nextAnimationFrame() {
    return new Promise(function resolveOnNextFrame(resolve) {
      window.requestAnimationFrame(function frameArrived() {
        resolve();
      });
    });
  }

  async function driveDeterministicRecording(playbackController) {
    const grid = compositor.forceDeterministicGridLayout(
      outputPixelWidth,
      outputPixelHeight,
    );
    const captureDurationSeconds =
      explicitCaptureDurationSeconds > 0
        ? explicitCaptureDurationSeconds
        : playbackController.totalCycleSeconds;
    const recordContext = compositor.createRecordCanvasContext(
      outputPixelWidth,
      outputPixelHeight,
    );
    const { muxer, videoEncoder } = encoder.createConfiguredMuxerAndEncoder(
      outputPixelWidth,
      outputPixelHeight,
      captureFramesPerSecond,
      targetBitsPerPixelPerFrame,
    );

    const totalFrameCount = Math.round(
      captureDurationSeconds * captureFramesPerSecond,
    );
    const microsecondsPerFrame = 1000000 / captureFramesPerSecond;
    const keyFrameIntervalFrames = Math.round(
      keyFrameIntervalSeconds * captureFramesPerSecond,
    );

    let activeSegmentHandle = null;
    let activeSegmentIndex = null;
    let panePlacements = [];

    for (let frameIndex = 0; frameIndex < totalFrameCount; frameIndex++) {
      const segment = playbackController.resolveSegment(
        frameIndex / captureFramesPerSecond,
      );
      if (segment.index !== activeSegmentIndex) {
        playbackController.destroySegment(activeSegmentHandle);
        playbackController.applyLayout(segment.index);
        await nextAnimationFrame();
        activeSegmentHandle = playbackController.buildSegment(segment.index);
        activeSegmentIndex = segment.index;
        await waitForSegmentAssetsToLoad(activeSegmentHandle);
        panePlacements = compositor.resolveFixedResolutionPanePlacements(
          activeSegmentHandle.renderers,
          grid,
          outputPixelWidth,
          outputPixelHeight,
        );
      }
      await compositor.prepareFixedResolutionFrame(
        panePlacements,
        segment.localElapsedSeconds,
      );
      compositor.renderFixedResolutionFrame(
        recordContext,
        panePlacements,
        segment.localElapsedSeconds,
        outputPixelWidth,
        outputPixelHeight,
      );
      const videoFrame = new VideoFrame(recordContext.canvas, {
        timestamp: Math.round(frameIndex * microsecondsPerFrame),
        duration: Math.round(microsecondsPerFrame),
      });
      videoEncoder.encode(videoFrame, {
        keyFrame: frameIndex % keyFrameIntervalFrames === 0,
      });
      videoFrame.close();
      if (videoEncoder.encodeQueueSize > encoderQueueHighWatermark) {
        await encoder.waitForEncoderQueueToDrain(
          videoEncoder,
          encoderQueueDrainTarget,
        );
      }
    }

    playbackController.destroySegment(activeSegmentHandle);
    await videoEncoder.flush();
    muxer.finalize();
    await encoder.uploadEncodedLoop(muxer.target.buffer, uploadUrl);
  }

  window.AMBIENT_CANVAS_RECORD_DRIVER = function startDeterministicRecording(
    playbackController,
  ) {
    driveDeterministicRecording(playbackController).catch(
      function reportRecordingFailure(recordingError) {
        console.error("ambient-canvas record: driver failed", recordingError);
      },
    );
  };
})();
