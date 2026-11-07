const SEEKABLE_VIDEO_SEEK_TIMEOUT_MILLISECONDS = 4000;
const SEEKABLE_VIDEO_SEEK_TOLERANCE_SECONDS = 0.004;
const SEEKABLE_VIDEO_END_OF_VIDEO_GUARD_SECONDS = 0.05;

function seekableVideoWaitForReady(videoElement) {
  return new Promise(function resolveWhenReady(resolve) {
    if (videoElement.readyState >= 2) {
      resolve();
      return;
    }
    function settle() {
      videoElement.removeEventListener("loadeddata", settle);
      videoElement.removeEventListener("error", settle);
      resolve();
    }
    videoElement.addEventListener("loadeddata", settle);
    videoElement.addEventListener("error", settle);
  });
}

function seekableVideoResolveLoopedSeekSeconds(
  videoElement,
  startSeconds,
  localElapsedSeconds,
) {
  const requestedSeconds = startSeconds + localElapsedSeconds;
  if (!videoElement.duration || !isFinite(videoElement.duration)) {
    return requestedSeconds;
  }
  const playableEndSeconds =
    videoElement.duration - SEEKABLE_VIDEO_END_OF_VIDEO_GUARD_SECONDS;
  const loopableSeconds = playableEndSeconds - startSeconds;
  if (loopableSeconds <= 0 || requestedSeconds < playableEndSeconds) {
    return requestedSeconds;
  }
  return startSeconds + (localElapsedSeconds % loopableSeconds);
}

function seekableVideoResolvePlayableDurationSeconds(videoElement) {
  if (!videoElement.duration || !isFinite(videoElement.duration)) {
    return 0;
  }
  return Math.max(
    0,
    videoElement.duration - SEEKABLE_VIDEO_END_OF_VIDEO_GUARD_SECONDS,
  );
}

function seekableVideoSeekTo(videoElement, targetSeconds) {
  if (!videoElement.duration || !isFinite(videoElement.duration)) {
    return Promise.resolve();
  }
  const clampedSeconds = Math.min(
    Math.max(0, targetSeconds),
    Math.max(
      0,
      videoElement.duration - SEEKABLE_VIDEO_END_OF_VIDEO_GUARD_SECONDS,
    ),
  );
  if (
    Math.abs(videoElement.currentTime - clampedSeconds) <
    SEEKABLE_VIDEO_SEEK_TOLERANCE_SECONDS
  ) {
    return Promise.resolve();
  }
  return new Promise(function resolveWhenSeeked(resolve) {
    let hasSettled = false;
    let timeoutId = 0;
    function settle() {
      if (hasSettled) {
        return;
      }
      hasSettled = true;
      videoElement.removeEventListener("seeked", settle);
      window.clearTimeout(timeoutId);
      resolve();
    }
    timeoutId = window.setTimeout(
      settle,
      SEEKABLE_VIDEO_SEEK_TIMEOUT_MILLISECONDS,
    );
    videoElement.addEventListener("seeked", settle);
    videoElement.currentTime = clampedSeconds;
  });
}

window.AmbientCanvasSeekableVideoSource = (function buildSeekableVideoSource() {
  function createSeekableVideoSource(
    videoUrl,
    startSeconds,
    seeksDeterministically,
  ) {
    const videoElement = document.createElement("video");
    videoElement.muted = true;
    videoElement.playsInline = true;
    videoElement.preload = "auto";
    videoElement.src = videoUrl;

    const deterministicVideoStepper = seeksDeterministically
      ? window.AmbientCanvasDeterministicVideoStepper.createDeterministicVideoStepper(
          videoElement,
          startSeconds,
          seekableVideoSeekTo,
          function resolveTargetSeconds(localElapsedSeconds) {
            return seekableVideoResolveLoopedSeekSeconds(
              videoElement,
              startSeconds,
              localElapsedSeconds,
            );
          },
        )
      : null;

    const readyPromise = seekableVideoWaitForReady(videoElement).then(
      function positionAtStart() {
        if (seeksDeterministically) {
          return deterministicVideoStepper.initialize();
        }
        videoElement.loop = true;
        videoElement.currentTime = startSeconds;
        return videoElement.play().catch(function ignoreAutoplayRejection() {});
      },
    );

    return {
      ready: readyPromise,
      element: videoElement,
      resolvePlayableDurationSeconds() {
        return seekableVideoResolvePlayableDurationSeconds(videoElement);
      },
      prepareFrame(localElapsedSeconds) {
        if (!seeksDeterministically) {
          return Promise.resolve();
        }
        return deterministicVideoStepper.prepareFrame(localElapsedSeconds);
      },
      dispose() {
        videoElement.pause();
        videoElement.removeAttribute("src");
        videoElement.load();
      },
    };
  }

  return { createSeekableVideoSource: createSeekableVideoSource };
})();
