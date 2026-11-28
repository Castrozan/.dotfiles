{
  const encoderQueueHighWatermark = 8;
  const encoderQueueDrainTarget = 4;
  const microsecondsPerSecond = 1000000;

  const createVideoFrame = (canvas, frameIndex, framesPerSecond) =>
    new VideoFrame(canvas, {
      timestamp: Math.round(
        (frameIndex * microsecondsPerSecond) / framesPerSecond,
      ),
      duration:
        Math.round(
          ((frameIndex + 1) * microsecondsPerSecond) / framesPerSecond,
        ) - Math.round((frameIndex * microsecondsPerSecond) / framesPerSecond),
    });

  const createConfiguredMuxerAndEncoder = (
    outputPixelWidth,
    outputPixelHeight,
    captureFramesPerSecond,
    targetBitsPerPixelPerFrame,
  ) => {
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
      output: (encodedChunk, chunkMetadata) =>
        muxer.addVideoChunk(encodedChunk, chunkMetadata),
      error: (encodeError) =>
        console.error("ambient-canvas record: encode error", encodeError),
    });
    videoEncoder.configure({
      codec: "avc1.640033",
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
  };

  const applyEncoderBackpressure = async (videoEncoder) => {
    if (videoEncoder.encodeQueueSize <= encoderQueueHighWatermark) {
      return;
    }
    while (videoEncoder.encodeQueueSize > encoderQueueDrainTarget) {
      await new Promise((resolve) => window.setTimeout(resolve, 4));
    }
  };

  const uploadRecordedSegment = async (
    encodedBuffer,
    segmentFingerprint,
    durationSeconds,
    uploadUrl,
  ) => {
    if (!uploadUrl) {
      return false;
    }
    const segmentQuery = new URLSearchParams({
      extension: "mp4",
      fingerprint: segmentFingerprint,
      seconds: String(durationSeconds),
    });
    try {
      const response = await fetch(`${uploadUrl}?${segmentQuery}`, {
        method: "POST",
        body: new Blob([encodedBuffer], { type: "video/mp4" }),
      });
      return response.ok;
    } catch {
      return false;
    }
  };

  const reportRecordingProgress = (uploadUrl) => {
    if (uploadUrl) {
      fetch(`${uploadUrl}?kind=progress`, { method: "POST" }).catch(() => {});
    }
  };

  const uploadSegmentManifest = async (manifestSegments, uploadUrl) => {
    if (!uploadUrl) {
      return;
    }
    try {
      await fetch(`${uploadUrl}?kind=manifest`, {
        method: "POST",
        body: JSON.stringify({ segments: manifestSegments }),
      });
    } catch {
      console.error("ambient-canvas record: manifest upload failed");
    } finally {
      window.setTimeout(() => window.close(), 250);
    }
  };

  window.AmbientCanvasRecordingEncoder = {
    createVideoFrame,
    createConfiguredMuxerAndEncoder,
    applyEncoderBackpressure,
    uploadRecordedSegment,
    reportRecordingProgress,
    uploadSegmentManifest,
  };
}
