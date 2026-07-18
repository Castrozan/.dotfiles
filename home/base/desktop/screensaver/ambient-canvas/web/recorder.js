(function installAmbientCanvasRecorder() {
  const recordParameters = new URLSearchParams(window.location.search);
  if (!recordParameters.has("record")) {
    return;
  }

  const captureDurationSeconds = Number(recordParameters.get("seconds")) || 30;
  const captureFramesPerSecond = Number(recordParameters.get("fps")) || 30;
  const uploadUrl = recordParameters.get("uploadUrl") || "";
  const layoutSettleMilliseconds = 1000;

  window.AMBIENT_CANVAS_RENDERER_OPTION_OVERRIDES = {
    preserveDrawingBuffer: true,
  };

  const hardwareDecodablePreferredMimeTypes = [
    "video/mp4;codecs=avc1",
    "video/mp4",
    "video/webm;codecs=vp9",
    "video/webm;codecs=vp8",
    "video/webm",
  ];

  function resolveSupportedMimeType() {
    for (const candidate of hardwareDecodablePreferredMimeTypes) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported(candidate)) {
        return candidate;
      }
    }
    return "";
  }

  function containerExtensionForMimeType(mimeType) {
    return mimeType.indexOf("mp4") !== -1 ? "mp4" : "webm";
  }

  const ambientCanvasGrid = document.getElementById("ambient-canvas-grid");

  const recordCanvas = document.createElement("canvas");
  recordCanvas.style.position = "fixed";
  recordCanvas.style.left = "0";
  recordCanvas.style.top = "0";
  recordCanvas.style.pointerEvents = "none";
  recordCanvas.style.opacity = "0";
  const recordContext = recordCanvas.getContext("2d");
  document.body.appendChild(recordCanvas);

  const recordedChunks = [];
  let mediaRecorder = null;
  let firstLaidOutFrameTimestamp = null;

  function compositePanesForFrame(activeRenderers, gridBounds) {
    const horizontalScale = recordCanvas.width / gridBounds.width;
    const verticalScale = recordCanvas.height / gridBounds.height;
    recordContext.fillStyle = "#0a1a2f";
    recordContext.fillRect(0, 0, recordCanvas.width, recordCanvas.height);
    for (const activeRenderer of activeRenderers) {
      const bounds = activeRenderer.canvasElement.getBoundingClientRect();
      if (bounds.width < 1 || bounds.height < 1) {
        continue;
      }
      recordContext.drawImage(
        activeRenderer.canvasElement,
        Math.round((bounds.left - gridBounds.left) * horizontalScale),
        Math.round((bounds.top - gridBounds.top) * verticalScale),
        Math.round(bounds.width * horizontalScale),
        Math.round(bounds.height * verticalScale),
      );
    }
  }

  function beginRecording(settledGridBounds) {
    const devicePixelRatio = window.devicePixelRatio || 1;
    recordCanvas.width = Math.max(
      2,
      Math.round(settledGridBounds.width * devicePixelRatio),
    );
    recordCanvas.height = Math.max(
      2,
      Math.round(settledGridBounds.height * devicePixelRatio),
    );

    const selectedMimeType = resolveSupportedMimeType();
    const containerExtension = containerExtensionForMimeType(selectedMimeType);
    const mediaStream = recordCanvas.captureStream(captureFramesPerSecond);
    mediaRecorder = new MediaRecorder(
      mediaStream,
      selectedMimeType ? { mimeType: selectedMimeType } : undefined,
    );
    mediaRecorder.ondataavailable = function collectChunk(dataEvent) {
      if (dataEvent.data && dataEvent.data.size > 0) {
        recordedChunks.push(dataEvent.data);
      }
    };
    mediaRecorder.onstop = function uploadRecording() {
      const recordedBlob = new Blob(recordedChunks, {
        type: selectedMimeType || "video/webm",
      });
      if (!uploadUrl) {
        return;
      }
      fetch(uploadUrl + "?extension=" + containerExtension, {
        method: "POST",
        body: recordedBlob,
      })
        .catch(function ignoreUploadFailure() {})
        .finally(function closeAfterUpload() {
          window.setTimeout(function requestWindowClose() {
            window.close();
          }, 250);
        });
    };
    mediaRecorder.start();
    window.setTimeout(function stopRecording() {
      if (mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
      }
    }, captureDurationSeconds * 1000);
  }

  window.AMBIENT_CANVAS_FRAME_OBSERVER = function observeFrame(
    activeRenderers,
  ) {
    if (!ambientCanvasGrid) {
      return;
    }
    const gridBounds = ambientCanvasGrid.getBoundingClientRect();
    if (gridBounds.width < 1 || gridBounds.height < 1) {
      return;
    }
    if (mediaRecorder === null) {
      if (firstLaidOutFrameTimestamp === null) {
        firstLaidOutFrameTimestamp = performance.now();
        return;
      }
      if (
        performance.now() - firstLaidOutFrameTimestamp <
        layoutSettleMilliseconds
      ) {
        return;
      }
      beginRecording(gridBounds);
    }
    compositePanesForFrame(activeRenderers, gridBounds);
  };
})();
