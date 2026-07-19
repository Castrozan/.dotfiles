window.AmbientCanvasSeekableVideoSource = (function buildSeekableVideoSource() {
  const SEEK_TIMEOUT_MILLISECONDS = 4000;
  const SEEK_TOLERANCE_SECONDS = 0.004;
  const END_OF_VIDEO_GUARD_SECONDS = 0.05;

  function waitForVideoReady(videoElement) {
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

  function seekVideoTo(videoElement, targetSeconds) {
    if (!videoElement.duration || !isFinite(videoElement.duration)) {
      return Promise.resolve();
    }
    const clampedSeconds = Math.min(
      Math.max(0, targetSeconds),
      Math.max(0, videoElement.duration - END_OF_VIDEO_GUARD_SECONDS),
    );
    if (
      Math.abs(videoElement.currentTime - clampedSeconds) <
      SEEK_TOLERANCE_SECONDS
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
      timeoutId = window.setTimeout(settle, SEEK_TIMEOUT_MILLISECONDS);
      videoElement.addEventListener("seeked", settle);
      videoElement.currentTime = clampedSeconds;
    });
  }

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

    const readyPromise = waitForVideoReady(videoElement).then(
      function positionAtStart() {
        if (seeksDeterministically) {
          return seekVideoTo(videoElement, startSeconds);
        }
        videoElement.loop = true;
        videoElement.currentTime = startSeconds;
        return videoElement.play().catch(function ignoreAutoplayRejection() {});
      },
    );

    return {
      ready: readyPromise,
      element: videoElement,
      prepareFrame(localElapsedSeconds) {
        if (!seeksDeterministically) {
          return Promise.resolve();
        }
        return seekVideoTo(videoElement, startSeconds + localElapsedSeconds);
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
