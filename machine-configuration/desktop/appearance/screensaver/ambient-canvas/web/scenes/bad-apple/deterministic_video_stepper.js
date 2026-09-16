window.AmbientCanvasDeterministicVideoStepper =
  (function buildDeterministicVideoStepper() {
    const FRAME_TIMEOUT_MILLISECONDS = 4000;
    const FRAME_TIME_TOLERANCE_SECONDS = 0.004;
    const CALIBRATION_LOOKBACK_SECONDS = 1;

    function resolveCalibrationStartSeconds(videoElement, startSeconds) {
      if (
        !Number.isFinite(videoElement.duration) ||
        videoElement.duration - startSeconds >= CALIBRATION_LOOKBACK_SECONDS
      ) {
        return startSeconds;
      }
      return Math.max(0, startSeconds - CALIBRATION_LOOKBACK_SECONDS);
    }

    function resolvePresentedMediaTimeBeforeStart(
      firstMediaTimeSeconds,
      sourceFrameDurationSeconds,
      startSeconds,
    ) {
      const elapsedSourceFrames = Math.floor(
        (startSeconds - firstMediaTimeSeconds + FRAME_TIME_TOLERANCE_SECONDS) /
          sourceFrameDurationSeconds,
      );
      return (
        firstMediaTimeSeconds + elapsedSourceFrames * sourceFrameDurationSeconds
      );
    }

    function waitForNextPresentedFrame(videoElement, previousMediaTimeSeconds) {
      return new Promise(function resolveWhenFrameAdvances(resolve, reject) {
        let callbackIdentifier = 0;
        const timeoutIdentifier = window.setTimeout(function rejectTimeout() {
          videoElement.pause();
          if (videoElement.cancelVideoFrameCallback) {
            videoElement.cancelVideoFrameCallback(callbackIdentifier);
          }
          reject(new Error("ambient-canvas video frame advance timed out"));
        }, FRAME_TIMEOUT_MILLISECONDS);

        function acceptAdvancedFrame(_currentTime, frameMetadata) {
          if (
            frameMetadata.mediaTime <=
            previousMediaTimeSeconds + FRAME_TIME_TOLERANCE_SECONDS
          ) {
            callbackIdentifier =
              videoElement.requestVideoFrameCallback(acceptAdvancedFrame);
            return;
          }
          videoElement.pause();
          window.clearTimeout(timeoutIdentifier);
          resolve(frameMetadata.mediaTime);
        }

        callbackIdentifier =
          videoElement.requestVideoFrameCallback(acceptAdvancedFrame);
        videoElement.play().catch(function rejectPlayback(playbackError) {
          videoElement.pause();
          if (videoElement.cancelVideoFrameCallback) {
            videoElement.cancelVideoFrameCallback(callbackIdentifier);
          }
          window.clearTimeout(timeoutIdentifier);
          reject(playbackError);
        });
      });
    }

    function createDeterministicVideoStepper(
      videoElement,
      startSeconds,
      seekVideoTo,
      resolveTargetSeconds,
    ) {
      let presentedMediaTimeSeconds = startSeconds;
      let sourceFrameDurationSeconds = 0;

      async function initialize() {
        const calibrationStartSeconds = resolveCalibrationStartSeconds(
          videoElement,
          startSeconds,
        );
        await seekVideoTo(videoElement, calibrationStartSeconds);
        const firstMediaTimeSeconds = await waitForNextPresentedFrame(
          videoElement,
          calibrationStartSeconds,
        );
        const secondMediaTimeSeconds = await waitForNextPresentedFrame(
          videoElement,
          firstMediaTimeSeconds,
        );
        sourceFrameDurationSeconds =
          secondMediaTimeSeconds - firstMediaTimeSeconds;
        await seekVideoTo(videoElement, startSeconds);
        presentedMediaTimeSeconds = resolvePresentedMediaTimeBeforeStart(
          firstMediaTimeSeconds,
          sourceFrameDurationSeconds,
          startSeconds,
        );
      }

      async function prepareFrame(localElapsedSeconds) {
        const targetSeconds = resolveTargetSeconds(localElapsedSeconds);
        if (
          targetSeconds <
          presentedMediaTimeSeconds - FRAME_TIME_TOLERANCE_SECONDS
        ) {
          await seekVideoTo(videoElement, targetSeconds);
          presentedMediaTimeSeconds = targetSeconds;
        }
        while (
          presentedMediaTimeSeconds + sourceFrameDurationSeconds <=
          targetSeconds + FRAME_TIME_TOLERANCE_SECONDS
        ) {
          const nextMediaTimeSeconds = await waitForNextPresentedFrame(
            videoElement,
            presentedMediaTimeSeconds,
          );
          sourceFrameDurationSeconds =
            nextMediaTimeSeconds - presentedMediaTimeSeconds;
          presentedMediaTimeSeconds = nextMediaTimeSeconds;
        }
      }

      return { initialize: initialize, prepareFrame: prepareFrame };
    }

    return {
      createDeterministicVideoStepper: createDeterministicVideoStepper,
    };
  })();
