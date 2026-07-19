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

  function uploadEncodedLoop(encodedBuffer, uploadUrl) {
    if (!uploadUrl) {
      return Promise.resolve();
    }
    return fetch(uploadUrl + "?extension=mp4", {
      method: "POST",
      body: new Blob([encodedBuffer], { type: "video/mp4" }),
    })
      .catch(function ignoreUploadFailure() {})
      .finally(function closeAfterUpload() {
        window.setTimeout(function requestWindowClose() {
          window.close();
        }, 250);
      });
  }

  return {
    createConfiguredMuxerAndEncoder,
    waitForEncoderQueueToDrain,
    uploadEncodedLoop,
  };
})();
