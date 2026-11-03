{
  const resolveRecordingParameters = (parameters) => {
    const numberOrDefault = (name, fallback) =>
      Number(parameters.get(name)) || fallback;
    const workerCount = numberOrDefault("workerCount", 1);
    return {
      explicitCaptureDurationSeconds: numberOrDefault("seconds", 0),
      captureFramesPerSecond: numberOrDefault("fps", 60),
      uploadUrl: parameters.get("uploadUrl") ?? "",
      themeBackgroundHex: parameters.get("themeBackground") ?? "",
      outputPixelWidth: numberOrDefault("width", 1920),
      outputPixelHeight: numberOrDefault("height", 1080),
      worker: {
        index: Number(parameters.get("workerIndex")),
        scheduledDurationSecondsByWorker: Array(workerCount).fill(0),
      },
    };
  };

  const assignSegmentRecording = (
    recordingRange,
    worker,
    segmentFingerprint,
    recordedFingerprints,
  ) => {
    const scheduledDurations = worker.scheduledDurationSecondsByWorker;
    const assignedWorkerIndex = scheduledDurations.indexOf(
      Math.min(...scheduledDurations),
    );
    scheduledDurations[assignedWorkerIndex] += recordingRange.durationSeconds;
    return (
      assignedWorkerIndex === worker.index &&
      !recordedFingerprints.has(segmentFingerprint)
    );
  };

  const waitForSegmentAssetsToLoad = (segmentHandle) => {
    return Promise.all(
      segmentHandle.renderers.map(function awaitOneRenderer(activeRenderer) {
        return activeRenderer.renderer.ready || Promise.resolve();
      }),
    );
  };

  const resolveSegmentRecordingSource = (segmentHandle) => {
    const recordingSources = segmentHandle.renderers
      .map(function resolveOneSource(activeRenderer) {
        if (!activeRenderer.renderer.resolveRecordingSource) {
          return null;
        }
        return activeRenderer.renderer.resolveRecordingSource();
      })
      .filter(Boolean);
    return recordingSources.length === 1 ? recordingSources[0] : null;
  };

  const normalizeSeconds = (seconds) => {
    return Math.round(seconds * 1000000) / 1000000;
  };

  const resolveRecordingRanges = (recordingSource, chunkDurationSeconds) => {
    if (!recordingSource) {
      return [{ startSeconds: 0, durationSeconds: chunkDurationSeconds }];
    }
    if (!hasPlayableRecordingSource(recordingSource)) {
      throw new Error("recording source has no playable duration");
    }
    const recordingRanges = [];
    for (
      let startSeconds = 0;
      startSeconds < recordingSource.durationSeconds;
      startSeconds += chunkDurationSeconds
    ) {
      recordingRanges.push({
        startSeconds: normalizeSeconds(startSeconds),
        durationSeconds: normalizeSeconds(
          Math.min(
            chunkDurationSeconds,
            recordingSource.durationSeconds - startSeconds,
          ),
        ),
        sequence: recordingSource.sequence,
      });
    }
    return recordingRanges;
  };

  const hasPlayableRecordingSource = (recordingSource) => {
    return (
      recordingSource.sequence &&
      Number.isFinite(recordingSource.durationSeconds) &&
      recordingSource.durationSeconds > 0
    );
  };

  const resolveCompositionRecordingRanges = async (
    playbackController,
    compositionIndex,
    chunkDurationSeconds,
    nextAnimationFrame,
  ) => {
    playbackController.applyLayout(compositionIndex);
    await nextAnimationFrame();
    const segmentHandle = playbackController.buildSegment(compositionIndex);
    await waitForSegmentAssetsToLoad(segmentHandle);
    const recordingSource = resolveSegmentRecordingSource(segmentHandle);
    playbackController.destroySegment(segmentHandle);
    return resolveRecordingRanges(recordingSource, chunkDurationSeconds);
  };

  const buildManifestSegment = (segmentFingerprint, recordingRange) => {
    const manifestSegment = {
      fingerprint: segmentFingerprint,
      extension: "mp4",
      durationSeconds: recordingRange.durationSeconds,
    };
    if (recordingRange.sequence) {
      manifestSegment.sequence = recordingRange.sequence;
    }
    return manifestSegment;
  };

  window.AmbientCanvasRecordingPlan = {
    resolveRecordingParameters,
    assignSegmentRecording,
    waitForSegmentAssetsToLoad,
    resolveRecordingRanges,
    resolveCompositionRecordingRanges,
    buildManifestSegment,
  };
}
