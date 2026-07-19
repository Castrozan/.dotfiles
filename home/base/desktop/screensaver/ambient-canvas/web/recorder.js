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
  const contentFillFraction = 0.9;
  const targetBitsPerPixelPerFrame = 0.35;
  const keyFrameIntervalSeconds = 2;
  const encoderQueueHighWatermark = 8;
  const encoderQueueDrainTarget = 4;

  const compositor = window.AmbientCanvasRecordingCompositor;
  const encoder = window.AmbientCanvasRecordingEncoder;

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

  async function driveDeterministicRecording(activeRenderers) {
    const grid = compositor.forceDeterministicGridLayout(
      outputPixelWidth,
      outputPixelHeight,
    );
    await nextAnimationFrame();
    const panePlacements = compositor.resolveFixedResolutionPanePlacements(
      activeRenderers,
      grid,
      outputPixelWidth,
      outputPixelHeight,
      contentFillFraction,
    );
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

    for (let frameIndex = 0; frameIndex < totalFrameCount; frameIndex++) {
      const elapsedSeconds = frameIndex / captureFramesPerSecond;
      compositor.renderFixedResolutionFrame(
        recordContext,
        panePlacements,
        elapsedSeconds,
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

    await videoEncoder.flush();
    muxer.finalize();
    await encoder.uploadEncodedLoop(muxer.target.buffer, uploadUrl);
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
