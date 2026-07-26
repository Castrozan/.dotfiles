window.AmbientCanvasRecordingEncoder = (function buildEncoder() {
  function createConfiguredMuxerAndEncoder(
    outputPixelWidth,
    outputPixelHeight,
    captureFramesPerSecond,
    targetBitsPerPixelPerFrame,
  ) {
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

  function waitForEncoderQueueToDrain(videoEncoder, encoderQueueDrainTarget) {
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

  function uploadRecordedSegment(
    encodedBuffer,
    segmentFingerprint,
    durationSeconds,
    uploadUrl,
  ) {
    if (!uploadUrl) {
      return Promise.resolve(false);
    }
    const segmentQuery = new URLSearchParams({
      extension: "mp4",
      fingerprint: segmentFingerprint,
      seconds: String(durationSeconds),
    });
    return fetch(uploadUrl + "?" + segmentQuery.toString(), {
      method: "POST",
      body: new Blob([encodedBuffer], { type: "video/mp4" }),
    })
      .then(function reportStorageOutcome(response) {
        return response.ok;
      })
      .catch(function ignoreSegmentUploadFailure() {
        return false;
      });
  }

  function uploadSegmentManifest(manifestSegments, uploadUrl) {
    if (!uploadUrl) {
      return Promise.resolve();
    }
    return fetch(uploadUrl + "?kind=manifest", {
      method: "POST",
      body: JSON.stringify({ segments: manifestSegments }),
    })
      .catch(function ignoreManifestUploadFailure() {})
      .finally(function closeAfterManifestUpload() {
        window.setTimeout(function requestWindowClose() {
          window.close();
        }, 250);
      });
  }

  return {
    createConfiguredMuxerAndEncoder,
    waitForEncoderQueueToDrain,
    uploadRecordedSegment,
    uploadSegmentManifest,
  };
})();
