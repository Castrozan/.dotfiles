const fs = require("fs");
const path = require("path");
const webDirectory = process.argv[2];
const recordUrl = new URL(process.argv[3]);
const uploadLimit = Number(process.argv[4]);
const encodedCompositions = [];
let currentComposition;
let uploadCount = 0;
global.window = global;
global.crypto = require("crypto").webcrypto;
window.location = { search: recordUrl.search };
window.requestAnimationFrame = (callback) => callback();
window.close = () => {};
function loadSource(relativePath) {
  eval(fs.readFileSync(path.join(webDirectory, relativePath), "utf8"));
}
loadSource("record/ambient-canvas-recording-encoder.js");
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
  async uploadRecordedSegment(...arguments) {
    const stored = await originalEncoder.uploadRecordedSegment(...arguments);
    if (!stored) throw new Error("segment upload failed");
    uploadCount++;
    if (uploadLimit && uploadCount >= uploadLimit) {
      process.stdout.write(JSON.stringify(encodedCompositions));
      process.exit(77);
    }
    return stored;
  },
  async uploadSegmentManifest(...arguments) {
    await originalEncoder.uploadSegmentManifest(...arguments);
    process.stdout.write(JSON.stringify(encodedCompositions));
  },
};
window.AmbientCanvasRecordingPlan = {
  async waitForSegmentAssetsToLoad() {},
  async resolveCompositionRecordingRanges() {
    return [0, 1].map((startSeconds) => ({ durationSeconds: 1, startSeconds }));
  },
  buildManifestSegment(fingerprint, range) {
    return { fingerprint, durationSeconds: range.durationSeconds };
  },
};
loadSource("recorder.js");
window.AMBIENT_CANVAS_RECORD_DRIVER({
  compositions: [0, 1, 2, 3].map((index) => ({ panes: [], index })),
  applyLayout(index) {
    currentComposition = index;
  },
  buildSegment() {
    return { renderers: [] };
  },
  destroySegment() {},
});
