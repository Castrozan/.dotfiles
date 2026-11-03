import json
import pathlib
import subprocess

from recording.recorded_loop_capture_plan import DEFAULT_CAPTURE_FRAMES_PER_SECOND


RECORDER_PATH = pathlib.Path(__file__).resolve().parents[3] / "web" / "recorder.js"


def test_launcher_defaults_to_sixty_frames_per_second():
    assert DEFAULT_CAPTURE_FRAMES_PER_SECOND == 60


def test_recorder_produces_contiguous_sixty_frame_timestamps():
    source = r"""
global.window = global;
const frames = [];
window.location = { search: '?record=1&seconds=3' };
window.requestAnimationFrame = callback => callback();
eval(require('fs').readFileSync(process.argv[2], 'utf8'));
window.AmbientCanvasRecordingCompositor = {
  forceDeterministicGridLayout() {},
  createRecordCanvasContext() { return {canvas: {}}; },
  resolveFixedResolutionPanePlacements() { return []; },
  async prepareFixedResolutionFrame() {},
  renderFixedResolutionFrame() {},
};
window.AmbientCanvasRecordingEncoder = {
  createVideoFrame: window.AmbientCanvasRecordingEncoder.createVideoFrame,
  createConfiguredMuxerAndEncoder(width, height, framesPerSecond) {
    return {
      muxer: {finalize() {}, target: {buffer: new ArrayBuffer(0)}},
      videoEncoder: {
        encodeQueueSize: 0,
        encode(frame, options) { frames.push({...frame.options, ...options}); },
        async flush() {},
      },
    };
  },
  async uploadRecordedSegment() {},
  async uploadSegmentManifest() {
    process.stdout.write(JSON.stringify(frames));
  },
};
window.AmbientCanvasRecordingFingerprint = {
  async fetchSegmentFingerprintInputs() { return {}; },
  async fetchRecordedSegmentFingerprints() { return new Set(); },
  async resolveCompositionFingerprint() { return 'segment'; },
};
eval(require("fs").readFileSync(process.argv[3], "utf8"));
window.AmbientCanvasRecordingPlan = {
  ...window.AmbientCanvasRecordingPlan,
  async waitForSegmentAssetsToLoad() {},
  async resolveCompositionRecordingRanges() {
    return [{durationSeconds: 3, startSeconds: 0}];
  },
  buildManifestSegment() { return {}; },
};
global.VideoFrame = class {
  constructor(canvas, options) { this.options = options; }
  close() {}
};
eval(require('fs').readFileSync(process.argv[1], 'utf8'));
window.AMBIENT_CANVAS_RECORD_DRIVER({
  compositions: [{}],
  applyLayout() {},
  buildSegment() { return {renderers: []}; },
  destroySegment() {},
});
"""
    completed = subprocess.run(
        [
            "node",
            "-e",
            source,
            str(RECORDER_PATH),
            str(
                RECORDER_PATH.parent / "record" / "ambient-canvas-recording-encoder.js"
            ),
            str(RECORDER_PATH.parent / "record" / "ambient-canvas-recording-plan.js"),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    frames = json.loads(completed.stdout)
    assert len(frames) == 180
    assert frames[0]["timestamp"] == 0
    assert frames[-1]["timestamp"] + frames[-1]["duration"] == 3_000_000
    assert all(
        current["timestamp"] + current["duration"] == following["timestamp"]
        for current, following in zip(frames, frames[1:], strict=False)
    )
    assert [index for index, frame in enumerate(frames) if frame["keyFrame"]] == [
        0,
        120,
    ]
