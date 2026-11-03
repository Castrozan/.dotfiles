window.AmbientCanvasRecordingFingerprint =
  (function buildRecordingFingerprint() {
    const SEGMENT_FINGERPRINT_INPUTS_PATH = "/segment-fingerprint-inputs";
    const RECORDED_SEGMENT_INVENTORY_PATH = "/recorded-segment-fingerprints";

    async function fetchJsonFromRecordServer(uploadUrl, endpointPath) {
      const response = await fetch(new URL(endpointPath, uploadUrl).toString());
      if (!response.ok) {
        throw new Error(
          `recording metadata request failed: ${response.status}`,
        );
      }
      return response.json();
    }

    function fetchSegmentFingerprintInputs(uploadUrl) {
      return fetchJsonFromRecordServer(
        uploadUrl,
        SEGMENT_FINGERPRINT_INPUTS_PATH,
      );
    }

    async function fetchRecordedSegmentFingerprints(uploadUrl) {
      const inventory = await fetchJsonFromRecordServer(
        uploadUrl,
        RECORDED_SEGMENT_INVENTORY_PATH,
      );
      return new Set(inventory.fingerprints);
    }

    function encodeDigestAsHexadecimal(digestBuffer) {
      return Array.from(new Uint8Array(digestBuffer))
        .map(function toHexadecimalByte(digestByte) {
          return digestByte.toString(16).padStart(2, "0");
        })
        .join("");
    }

    function resolveComposedSceneDigests(composition, fingerprintInputs) {
      return (composition.panes || []).map(
        function digestOnePane(paneConfiguration) {
          return (
            fingerprintInputs.scenes[paneConfiguration.scene] ||
            "unregistered-scene:" + paneConfiguration.scene
          );
        },
      );
    }

    async function resolveCompositionFingerprint(
      composition,
      durationSeconds,
      fingerprintInputs,
      captureSignature,
      themeBackgroundHex,
      recordingStartSeconds,
    ) {
      const fingerprintSource = JSON.stringify({
        composition: composition,
        durationSeconds: durationSeconds,
        scenes: resolveComposedSceneDigests(composition, fingerprintInputs),
        pipeline: fingerprintInputs.pipeline,
        capture: captureSignature,
        themeBackground: themeBackgroundHex,
        recordingStartSeconds: recordingStartSeconds,
      });
      const digestBuffer = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(fingerprintSource),
      );
      return encodeDigestAsHexadecimal(digestBuffer);
    }

    return {
      fetchSegmentFingerprintInputs,
      fetchRecordedSegmentFingerprints,
      resolveCompositionFingerprint,
    };
  })();
