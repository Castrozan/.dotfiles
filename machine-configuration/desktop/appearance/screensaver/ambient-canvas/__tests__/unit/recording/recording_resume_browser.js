const fs = require("node:fs");
const path = require("node:path");
const webDirectory = process.argv[2];
const recordUrl = new URL(process.argv[3]);
const uploadLimit = Number(process.argv[4]);
const encodedCompositions = [];
let currentComposition;
let uploadCount = 0;
global.window = global;
global.crypto = require("node:crypto").webcrypto;
window.location = { search: recordUrl.search };
window.requestAnimationFrame = (callback) => callback();
window.close = () => {};
function loadSource(relativePath) {
  require("node:vm").runInThisContext(
    fs.readFileSync(path.join(webDirectory, relativePath), "utf8"),
  );
}
loadSource("record/ambient-canvas-recording-encoder.js");
loadSource("record/ambient-canvas-recording-plan.js");
loadSource("record/ambient-canvas-recording-fingerprint.js");
const originalEncoder = window.AmbientCanvasRecordingEncoder;
window.AmbientCanvasRecordingCompositor = {
  forceDeterministicGridLayout() {},
  createRecordCanvasContext() {
    return { canvas: {} };
  },
  resolveFixedResolutionPanePlacements() {
    return [];
  },
  async prepareFixedResolutionFrame() {},
  renderFixedResolutionFrame() {},
};
window.AmbientCanvasRecordingEncoder = {
  createVideoFrame() {
    return { close() {} };
  },
  createConfiguredMuxerAndEncoder() {
    encodedCompositions.push(currentComposition);
    return {
      muxer: { finalize() {}, target: { buffer: new ArrayBuffer(4000) } },
      videoEncoder: {
        encodeQueueSize: 0,
        encode() {},
        async flush() {},
      },
    };
  },
  async uploadRecordedSegment(...uploadArguments) {
    const stored = await originalEncoder.uploadRecordedSegment(
      ...uploadArguments,
    );
    if (!stored) throw new Error("segment upload failed");
    uploadCount++;
    if (uploadLimit && uploadCount >= uploadLimit) {
      process.stdout.write(JSON.stringify(encodedCompositions));
      process.exit(77);
    }
    return stored;
  },
  async uploadSegmentManifest(...uploadArguments) {
    await originalEncoder.uploadSegmentManifest(...uploadArguments);
    process.stdout.write(JSON.stringify(encodedCompositions));
  },
};
window.AmbientCanvasRecordingPlan = {
  ...window.AmbientCanvasRecordingPlan,
  async waitForSegmentAssetsToLoad() {},
  async resolveCompositionRecordingRanges() {
    return Array.from(
      { length: Number(process.argv[6]) },
      (_, startSeconds) => ({ durationSeconds: 1, startSeconds }),
    );
  },
  buildManifestSegment(fingerprint, range) {
    return { fingerprint, durationSeconds: range.durationSeconds };
  },
};
loadSource("recorder.js");
window.AMBIENT_CANVAS_RECORD_DRIVER({
  compositions: Array.from({ length: Number(process.argv[5]) }, (_, index) => ({
    panes: [],
    index,
  })),
  applyLayout(index) {
    currentComposition = index;
  },
  buildSegment() {
    return { renderers: [] };
  },
  destroySegment() {},
});
