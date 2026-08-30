window.AmbientCanvasRecordingPlan = (function buildRecordingPlan() {
  function waitForSegmentAssetsToLoad(segmentHandle) {
    return Promise.all(
      segmentHandle.renderers.map(function awaitOneRenderer(activeRenderer) {
        return activeRenderer.renderer.ready || Promise.resolve();
      }),
    );
  }

  function resolveSegmentRecordingSource(segmentHandle) {
    const recordingSources = segmentHandle.renderers
      .map(function resolveOneSource(activeRenderer) {
        if (!activeRenderer.renderer.resolveRecordingSource) {
          return null;
        }
        return activeRenderer.renderer.resolveRecordingSource();
      })
      .filter(Boolean);
    return recordingSources.length === 1 ? recordingSources[0] : null;
  }

  function normalizeSeconds(seconds) {
    return Math.round(seconds * 1000000) / 1000000;
  }

  function resolveRecordingRanges(recordingSource, chunkDurationSeconds) {
    if (
      !recordingSource ||
      !recordingSource.sequence ||
      !Number.isFinite(recordingSource.durationSeconds) ||
      recordingSource.durationSeconds <= 0
    ) {
      return [{ startSeconds: 0, durationSeconds: chunkDurationSeconds }];
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
  }

  async function resolveCompositionRecordingRanges(
    playbackController,
    compositionIndex,
    chunkDurationSeconds,
    nextAnimationFrame,
  ) {
    playbackController.applyLayout(compositionIndex);
    await nextAnimationFrame();
    const segmentHandle = playbackController.buildSegment(compositionIndex);
    await waitForSegmentAssetsToLoad(segmentHandle);
    const recordingSource = resolveSegmentRecordingSource(segmentHandle);
    playbackController.destroySegment(segmentHandle);
    return resolveRecordingRanges(recordingSource, chunkDurationSeconds);
  }

  function buildManifestSegment(segmentFingerprint, recordingRange) {
    const manifestSegment = {
      fingerprint: segmentFingerprint,
      extension: "mp4",
      durationSeconds: recordingRange.durationSeconds,
    };
    if (recordingRange.sequence) {
      manifestSegment.sequence = recordingRange.sequence;
    }
    return manifestSegment;
  }

  return {
    waitForSegmentAssetsToLoad,
    resolveRecordingRanges,
    resolveCompositionRecordingRanges,
    buildManifestSegment,
  };
})();
