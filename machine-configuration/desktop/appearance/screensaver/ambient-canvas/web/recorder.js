{
  const recorderParameters = new URLSearchParams(window.location.search);
  const recorderPlan = window.AmbientCanvasRecordingPlan;
  const recorderTargetBitsPerPixelPerFrame = 0.35;
  const recorderKeyFrameIntervalSeconds = 2;
  const recorderEncoderQueueHighWatermark = 8;
  const recorderEncoderQueueDrainTarget = 4;

  const recorderCompositor = window.AmbientCanvasRecordingCompositor;
  const recorderEncoder = window.AmbientCanvasRecordingEncoder;
  const recorderFingerprint = window.AmbientCanvasRecordingFingerprint;

  const recorderNextAnimationFrame = () =>
    new Promise((resolve) => window.requestAnimationFrame(resolve));

  const recorderRecordOneComposition = async (
    recordingParameters,
    renderSurface,
    playbackController,
    compositionIndex,
    recordingRange,
  ) => {
    const { outputPixelWidth, outputPixelHeight, captureFramesPerSecond } =
      recordingParameters;
    playbackController.applyLayout(compositionIndex);
    await recorderNextAnimationFrame();
    const segmentHandle = playbackController.buildSegment(compositionIndex, {
      startSeconds: recordingRange.startSeconds,
    });
    await recorderPlan.waitForSegmentAssetsToLoad(segmentHandle);
    const panePlacements =
      recorderCompositor.resolveFixedResolutionPanePlacements(
        segmentHandle.renderers,
        renderSurface.deterministicGrid,
        outputPixelWidth,
        outputPixelHeight,
      );

    const { muxer, videoEncoder } =
      recorderEncoder.createConfiguredMuxerAndEncoder(
        outputPixelWidth,
        outputPixelHeight,
        captureFramesPerSecond,
        recorderTargetBitsPerPixelPerFrame,
      );
    const totalFrameCount = Math.round(
      recordingRange.durationSeconds * captureFramesPerSecond,
    );
    const keyFrameIntervalFrames = Math.round(
      recorderKeyFrameIntervalSeconds * captureFramesPerSecond,
    );

    for (let frameIndex = 0; frameIndex < totalFrameCount; frameIndex++) {
      const localElapsedSeconds = frameIndex / captureFramesPerSecond;
      await recorderCompositor.prepareFixedResolutionFrame(
        panePlacements,
        localElapsedSeconds,
      );
      recorderCompositor.renderFixedResolutionFrame(
        renderSurface.recordContext,
        panePlacements,
        localElapsedSeconds,
        outputPixelWidth,
        outputPixelHeight,
      );
      const videoFrame = recorderEncoder.createVideoFrame(
        renderSurface.recordContext.canvas,
        frameIndex,
        captureFramesPerSecond,
      );
      videoEncoder.encode(videoFrame, {
        keyFrame: frameIndex % keyFrameIntervalFrames === 0,
      });
      videoFrame.close();
      if (videoEncoder.encodeQueueSize > recorderEncoderQueueHighWatermark) {
        await recorderEncoder.waitForEncoderQueueToDrain(
          videoEncoder,
          recorderEncoderQueueDrainTarget,
        );
      }
    }

    playbackController.destroySegment(segmentHandle);
    await videoEncoder.flush();
    muxer.finalize();
    return muxer.target.buffer;
  };

  const recorderDriveDeterministicRecording = async (
    recordingParameters,
    playbackController,
  ) => {
    const renderSurface = {
      deterministicGrid: recorderCompositor.forceDeterministicGridLayout(
        recordingParameters.outputPixelWidth,
        recordingParameters.outputPixelHeight,
      ),
      recordContext: recorderCompositor.createRecordCanvasContext(
        recordingParameters.outputPixelWidth,
        recordingParameters.outputPixelHeight,
      ),
    };
    const { uploadUrl, themeBackgroundHex, worker } = recordingParameters;
    const fingerprintInputs =
      await recorderFingerprint.fetchSegmentFingerprintInputs(uploadUrl);
    const alreadyRecordedFingerprints =
      await recorderFingerprint.fetchRecordedSegmentFingerprints(uploadUrl);
    const captureSignature = {
      width: recordingParameters.outputPixelWidth,
      height: recordingParameters.outputPixelHeight,
      framesPerSecond: recordingParameters.captureFramesPerSecond,
      bitsPerPixelPerFrame: recorderTargetBitsPerPixelPerFrame,
      keyFrameIntervalSeconds: recorderKeyFrameIntervalSeconds,
    };
    const manifestSegments = [];

    for (
      let compositionIndex = 0;
      compositionIndex < playbackController.compositions.length;
      compositionIndex++
    ) {
      const composition = playbackController.compositions[compositionIndex];
      const chunkDurationSeconds =
        recordingParameters.explicitCaptureDurationSeconds > 0
          ? recordingParameters.explicitCaptureDurationSeconds
          : playbackController.compositionDurationSeconds(composition);
      const recordingRanges =
        await recorderPlan.resolveCompositionRecordingRanges(
          playbackController,
          compositionIndex,
          chunkDurationSeconds,
          recorderNextAnimationFrame,
        );
      for (const recordingRange of recordingRanges) {
        const segmentFingerprint =
          await recorderFingerprint.resolveCompositionFingerprint(
            composition,
            recordingRange.durationSeconds,
            fingerprintInputs,
            captureSignature,
            themeBackgroundHex,
            recordingRange.startSeconds,
          );
        manifestSegments.push(
          recorderPlan.buildManifestSegment(segmentFingerprint, recordingRange),
        );
        if (
          !recorderPlan.assignSegmentRecording(
            recordingRange,
            worker,
            segmentFingerprint,
            alreadyRecordedFingerprints,
          )
        ) {
          continue;
        }
        const encodedBuffer = await recorderRecordOneComposition(
          recordingParameters,
          renderSurface,
          playbackController,
          compositionIndex,
          recordingRange,
        );
        await recorderEncoder.uploadRecordedSegment(
          encodedBuffer,
          segmentFingerprint,
          recordingRange.durationSeconds,
          uploadUrl,
        );
        alreadyRecordedFingerprints.add(segmentFingerprint);
      }
    }

    await recorderEncoder.uploadSegmentManifest(manifestSegments, uploadUrl);
  };

  if (recorderParameters.has("record")) {
    const recordingParameters =
      recorderPlan.resolveRecordingParameters(recorderParameters);
    window.AMBIENT_CANVAS_RENDERER_OPTION_OVERRIDES = {
      preserveDrawingBuffer: true,
      deterministicPlayback: true,
    };
    window.AMBIENT_CANVAS_RECORD_DRIVER = function startDeterministicRecording(
      playbackController,
    ) {
      recorderDriveDeterministicRecording(
        recordingParameters,
        playbackController,
      ).catch(function reportRecordingFailure(recordingError) {
        console.error("ambient-canvas record: driver failed", recordingError);
        recorderEncoder.uploadSegmentManifest(
          [],
          recordingParameters.uploadUrl,
        );
      });
    };
  }
}
