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
  const fingerprint = window.AmbientCanvasRecordingFingerprint;

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

  function resolveCaptureSignature() {
    return {
      width: outputPixelWidth,
      height: outputPixelHeight,
      framesPerSecond: captureFramesPerSecond,
      bitsPerPixelPerFrame: targetBitsPerPixelPerFrame,
      keyFrameIntervalSeconds: keyFrameIntervalSeconds,
    };
  }

  async function recordOneComposition(
    playbackController,
    compositionIndex,
    durationSeconds,
    deterministicGrid,
    recordContext,
  ) {
    playbackController.applyLayout(compositionIndex);
    await nextAnimationFrame();
    const segmentHandle = playbackController.buildSegment(compositionIndex);
    await waitForSegmentAssetsToLoad(segmentHandle);
    const panePlacements = compositor.resolveFixedResolutionPanePlacements(
      segmentHandle.renderers,
      deterministicGrid,
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
      durationSeconds * captureFramesPerSecond,
    );
    const microsecondsPerFrame = 1000000 / captureFramesPerSecond;
    const keyFrameIntervalFrames = Math.round(
      keyFrameIntervalSeconds * captureFramesPerSecond,
    );

    for (let frameIndex = 0; frameIndex < totalFrameCount; frameIndex++) {
      const localElapsedSeconds = frameIndex / captureFramesPerSecond;
      await compositor.prepareFixedResolutionFrame(
        panePlacements,
        localElapsedSeconds,
      );
      compositor.renderFixedResolutionFrame(
        recordContext,
        panePlacements,
        localElapsedSeconds,
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

    playbackController.destroySegment(segmentHandle);
    await videoEncoder.flush();
    muxer.finalize();
    return muxer.target.buffer;
  }

  async function driveDeterministicRecording(playbackController) {
    const deterministicGrid = compositor.forceDeterministicGridLayout(
      outputPixelWidth,
      outputPixelHeight,
    );
    const recordContext = compositor.createRecordCanvasContext(
      outputPixelWidth,
      outputPixelHeight,
    );
    const fingerprintInputs =
      await fingerprint.fetchSegmentFingerprintInputs(uploadUrl);
    const alreadyRecordedFingerprints =
      await fingerprint.fetchRecordedSegmentFingerprints(uploadUrl);
    const captureSignature = resolveCaptureSignature();
    const manifestSegments = [];

    for (
      let compositionIndex = 0;
      compositionIndex < playbackController.compositions.length;
      compositionIndex++
    ) {
      const composition = playbackController.compositions[compositionIndex];
      const durationSeconds =
        explicitCaptureDurationSeconds > 0
          ? explicitCaptureDurationSeconds
          : playbackController.compositionDurationSeconds(composition);
      const segmentFingerprint =
        await fingerprint.resolveCompositionFingerprint(
          composition,
          durationSeconds,
          fingerprintInputs,
          captureSignature,
        );
      manifestSegments.push({
        fingerprint: segmentFingerprint,
        extension: "mp4",
        durationSeconds: durationSeconds,
      });
      if (alreadyRecordedFingerprints.has(segmentFingerprint)) {
        continue;
      }
      const encodedBuffer = await recordOneComposition(
        playbackController,
        compositionIndex,
        durationSeconds,
        deterministicGrid,
        recordContext,
      );
      await encoder.uploadRecordedSegment(
        encodedBuffer,
        segmentFingerprint,
        durationSeconds,
        uploadUrl,
      );
      alreadyRecordedFingerprints.add(segmentFingerprint);
    }

    await encoder.uploadSegmentManifest(manifestSegments, uploadUrl);
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
