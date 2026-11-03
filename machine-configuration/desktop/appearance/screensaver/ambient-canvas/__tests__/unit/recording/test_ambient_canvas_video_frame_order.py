import json
import pathlib
import subprocess


VIDEO_STEPPER_PATH = (
    pathlib.Path(__file__).resolve().parents[3]
    / "web/scenes/bad-apple/deterministic_video_stepper.js"
)


def resolve_recorded_frame_order(capture_times):
    source = r"""
global.window = global;
let presentedSeconds = 0;
let playCalls = 0;
const seekTargets = [];
const video = {
  duration: 120,
  requestVideoFrameCallback(callback) { this.callback = callback; return 1; },
  pause() {},
  play() {
    playCalls += 1;
    queueMicrotask(() => {
      presentedSeconds += playCalls === 3 ? 0.12 : 0.04;
      this.callback(0, {mediaTime: presentedSeconds});
    });
    return Promise.resolve();
  },
};
eval(require('fs').readFileSync(process.argv[1], 'utf8'));
(async () => {
  const stepper = AmbientCanvasDeterministicVideoStepper.createDeterministicVideoStepper(
    video, 0,
    async (video, target) => { seekTargets.push(target); presentedSeconds = target; },
    elapsedSeconds => elapsedSeconds,
  );
  await stepper.initialize();
  const times = [];
  for (const elapsedSeconds of JSON.parse(process.argv[2])) {
    await stepper.prepareFrame(elapsedSeconds);
    times.push(presentedSeconds);
  }
  process.stdout.write(JSON.stringify({seekTargets, times}));
})();
"""
    completed = subprocess.run(
        ["node", "-e", source, str(VIDEO_STEPPER_PATH), json.dumps(capture_times)],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return json.loads(completed.stdout)


def test_delayed_source_frames_do_not_rewind_a_forward_recording():
    result = resolve_recorded_frame_order([0.05, 0.066667, 0.083333, 0.1, 0.12, 0.16])
    assert result["seekTargets"] == [0, 0]
    assert result["times"] == sorted(result["times"])


def test_video_loops_still_seek_when_capture_time_moves_backwards():
    result = resolve_recorded_frame_order([0.05, 0.16, 0, 0.05])
    assert result["seekTargets"] == [0, 0, 0]
    assert result["times"] == [0.12, 0.16, 0, 0.04]
