import json
import pathlib
import subprocess

import pytest


AMBIENT_CANVAS_DIRECTORY = pathlib.Path(__file__).resolve().parents[2]
VIDEO_SOURCE_PATH = (
    AMBIENT_CANVAS_DIRECTORY
    / "web"
    / "scenes"
    / "bad-apple"
    / "seekable_video_source.js"
)
VIDEO_STEPPER_PATH = (
    AMBIENT_CANVAS_DIRECTORY
    / "web"
    / "scenes"
    / "bad-apple"
    / "deterministic_video_stepper.js"
)
DOCUMENT_SOURCE = (AMBIENT_CANVAS_DIRECTORY / "web" / "index.html").read_text()


def test_deterministic_capture_decodes_source_frames_sequentially():
    evaluation_source = f"""
global.window = global;
const frameDurationSeconds = 1 / 24;
const sourceFramePhaseSeconds = 0.01;
const state = {{ playCalls: 0, seekTargets: [] }};
const listeners = new Map();
const video = {{
  duration: 120,
  readyState: 2,
  paused: true,
  _currentTime: 30,
  presentedMediaTime: 30 - sourceFramePhaseSeconds,
  addEventListener(name, callback) {{ listeners.set(name, callback); }},
  removeEventListener(name) {{ listeners.delete(name); }},
  requestVideoFrameCallback(callback) {{ this.frameCallback = callback; }},
  play() {{
    this.paused = false;
    state.playCalls += 1;
    queueMicrotask(() => {{
      this.presentedMediaTime += frameDurationSeconds;
      this._currentTime = this.presentedMediaTime;
      const callback = this.frameCallback;
      this.frameCallback = null;
      callback(0, {{ mediaTime: this.presentedMediaTime }});
    }});
    return Promise.resolve();
  }},
  pause() {{ this.paused = true; }},
  removeAttribute() {{}},
  load() {{}},
  get currentTime() {{ return this._currentTime; }},
  set currentTime(value) {{
    this._currentTime = value;
    this.presentedMediaTime = value - sourceFramePhaseSeconds;
    state.seekTargets.push(value);
    queueMicrotask(() => listeners.get("seeked")?.());
  }},
}};
global.document = {{ createElement() {{ return video; }} }};
eval(require("fs").readFileSync({json.dumps(str(VIDEO_STEPPER_PATH))}, "utf8"));
eval(require("fs").readFileSync({json.dumps(str(VIDEO_SOURCE_PATH))}, "utf8"));
(async function () {{
  const source = global.AmbientCanvasSeekableVideoSource.createSeekableVideoSource(
    "video.mp4",
    30,
    true
  );
  await source.ready;
  const presentedTimes = [];
  for (const localElapsedSeconds of [0, 1 / 30, 2 / 30, 3 / 30]) {{
    await source.prepareFrame(localElapsedSeconds);
    presentedTimes.push(video.currentTime);
  }}
  process.stdout.write(JSON.stringify({{ ...state, presentedTimes }}));
}})();
"""
    completed = subprocess.run(
        ["node", "-e", evaluation_source],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    assert result["seekTargets"] == [30]
    assert result["playCalls"] == 4
    assert result["presentedTimes"] == pytest.approx(
        [
            30,
            30 - 0.01 + 1 / 24,
            30 - 0.01 + 1 / 24,
            30 - 0.01 + 2 / 24,
        ]
    )


def test_deterministic_capture_initializes_inside_a_subframe_video_tail():
    evaluation_source = f"""
global.window = global;
const nativeSetTimeout = global.setTimeout;
global.setTimeout = function scheduleImmediateTimeout(callback) {{
  return nativeSetTimeout(callback, 0);
}};
const durationSeconds = 180.093968;
const frameDurationSeconds = 1 / 24;
const startSeconds = 180;
const postSeekPhaseSeconds = 0.035;
const state = {{ playCalls: 0, seekTargets: [] }};
const listeners = new Map();
const video = {{
  duration: durationSeconds,
  readyState: 2,
  paused: true,
  _currentTime: 0,
  presentedMediaTime: postSeekPhaseSeconds,
  addEventListener(name, callback) {{ listeners.set(name, callback); }},
  removeEventListener(name) {{ listeners.delete(name); }},
  requestVideoFrameCallback(callback) {{
    this.frameCallback = callback;
    return 1;
  }},
  play() {{
    this.paused = false;
    state.playCalls += 1;
    const nextMediaTime = this.presentedMediaTime + frameDurationSeconds;
    if (nextMediaTime >= durationSeconds) {{
      return Promise.resolve();
    }}
    queueMicrotask(() => {{
      this.presentedMediaTime = nextMediaTime;
      this._currentTime = nextMediaTime;
      const callback = this.frameCallback;
      this.frameCallback = null;
      callback(0, {{ mediaTime: this.presentedMediaTime }});
    }});
    return Promise.resolve();
  }},
  pause() {{ this.paused = true; }},
  removeAttribute() {{}},
  load() {{}},
  get currentTime() {{ return this._currentTime; }},
  set currentTime(value) {{
    this._currentTime = value;
    this.presentedMediaTime = value + postSeekPhaseSeconds;
    state.seekTargets.push(value);
    queueMicrotask(() => listeners.get("seeked")?.());
  }},
}};
global.document = {{ createElement() {{ return video; }} }};
eval(require("fs").readFileSync({json.dumps(str(VIDEO_STEPPER_PATH))}, "utf8"));
eval(require("fs").readFileSync({json.dumps(str(VIDEO_SOURCE_PATH))}, "utf8"));
(async function () {{
  const source = global.AmbientCanvasSeekableVideoSource.createSeekableVideoSource(
    "video.mp4",
    startSeconds,
    true
  );
  await source.ready;
  const presentedTimes = [];
  for (const localElapsedSeconds of [0, 1 / 30]) {{
    await source.prepareFrame(localElapsedSeconds);
    presentedTimes.push(video.presentedMediaTime);
  }}
  process.stdout.write(JSON.stringify({{ ...state, presentedTimes }}));
}})();
"""
    completed = subprocess.run(
        ["node", "-e", evaluation_source],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    assert result["seekTargets"][0] < 180
    assert result["seekTargets"][-1] == 180
    assert result["playCalls"] == 3
    assert result["presentedTimes"] == pytest.approx(
        [180 + 0.035, 180 + 0.035 + 1 / 24]
    )


def test_video_stepper_loads_before_the_source_that_uses_it():
    assert DOCUMENT_SOURCE.index(
        "deterministic_video_stepper.js"
    ) < DOCUMENT_SOURCE.index("seekable_video_source.js")
