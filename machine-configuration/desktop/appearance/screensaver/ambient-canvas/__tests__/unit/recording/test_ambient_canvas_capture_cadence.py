import json
import pathlib
import subprocess

from recording.recorded_loop_capture_plan import DEFAULT_CAPTURE_FRAMES_PER_SECOND


RECORDER_PATH = pathlib.Path(__file__).resolve().parents[3] / "web" / "recorder.js"


def test_launcher_defaults_to_sixty_frames_per_second():
    assert DEFAULT_CAPTURE_FRAMES_PER_SECOND == 60


RECORDER_HARNESS_SOURCE = r"""
global.window = global;
const frames = [];
const configuredEncoders = [];
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
  createConfiguredMuxerAndEncoder(width, height, framesPerSecond, bitsPerPixelPerFrame) {
    configuredEncoders.push({width, height, framesPerSecond, bitsPerPixelPerFrame});
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
    process.stdout.write(JSON.stringify({frames, configuredEncoders}));
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


def record_three_seconds_with_stubbed_encoder():
    completed = subprocess.run(
        [
            "node",
            "-e",
            RECORDER_HARNESS_SOURCE,
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
    return json.loads(completed.stdout)


def test_recorder_produces_contiguous_sixty_frame_timestamps():
    frames = record_three_seconds_with_stubbed_encoder()["frames"]
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


def test_full_hd_bitrate_ceiling_stays_where_dense_line_art_still_reads_clean():
    configured_encoder = record_three_seconds_with_stubbed_encoder()[
        "configuredEncoders"
    ][0]
    bitrate_ceiling = (
        configured_encoder["width"]
        * configured_encoder["height"]
        * configured_encoder["framesPerSecond"]
        * configured_encoder["bitsPerPixelPerFrame"]
    )
    assert (configured_encoder["width"], configured_encoder["height"]) == (1920, 1080)
    assert 15_000_000 <= bitrate_ceiling <= 20_000_000
