import json
import shutil
import subprocess
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[3] / "renderer/camera-layer.js"

STUBS = r"""
const fs = require("node:fs");
class Scene { add(plane) { this.plane = plane; } }
class Camera { constructor() { this.position = {}; } }
class Material {}
class Geometry {}
class Mesh { constructor() { this.scale = { set: (...values) => { this.scales = values; } }; } }
class Texture { dispose() {} }
globalThis.avatarTestThree = { Scene, OrthographicCamera: Camera, MeshBasicMaterial: Material, PlaneGeometry: Geometry, Mesh, VideoTexture: Texture, CanvasTexture: Texture, sRGBEncoding: 3001 };
const drawing = { fillRect() {}, fillText() {} };
globalThis.document = { createElement: () => ({ videoWidth: 640, videoHeight: 480, play: async () => {}, getContext: () => drawing }) };
const source = fs.readFileSync(process.argv[1], "utf8").replace('import * as THREE from "three";', "const THREE = globalThis.avatarTestThree;").replace('"./camera-phase.js"', JSON.stringify(require("node:url").pathToFileURL(require("node:path").join(require("node:path").dirname(process.argv[1]), "camera-phase.js")).href));
"""

HARNESS = (
    STUBS
    + r"""
const scenario = process.argv[2];
const track = { label: scenario === "feedback" ? "Avatar Cam" : "USB Camera", stopped: 0, stop() { this.stopped++; }, addEventListener(name, callback) { this[name] = callback; } };
const stream = { getTracks: () => [track], getVideoTracks: () => [track] };
let constraints;
Object.defineProperty(globalThis, "navigator", { value: { mediaDevices: { getUserMedia: async value => { constraints = value; return stream; } } } });
(async () => {
  const { CameraLayer } = await import("data:text/javascript," + encodeURIComponent(source));
  let ended = 0;
  const layer = new CameraLayer(() => { ended++; });
  const draws = [];
  const renderer = { render: scene => draws.push(scene.plane.scales) };
  let error;
  if (scenario === "synthetic") layer.enableSynthetic();
  else { try { await layer.enable("chosen-camera"); } catch (failure) { error = failure.message; } }
  if (layer.active) layer.render(renderer, 100, 0.4);
  const wasActive = layer.active;
  if (scenario === "physical") track.ended();
  else layer.disable();
  console.log(JSON.stringify({ wasActive, active: layer.active, draws, stopped: track.stopped, ended, constraints, error }));
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
)

RACE_HARNESS = (
    STUBS
    + r"""
const scenario = process.argv[2];
const pendingRequests = [];
const pendingEnumerations = [];
Object.defineProperty(globalThis, "navigator", { value: { mediaDevices: { getUserMedia: () => new Promise(resolve => { pendingRequests.push(resolve); }), enumerateDevices: () => new Promise(resolve => { pendingEnumerations.push(resolve); }) } } });
const makeTrack = label => ({ label, stopped: 0, stop() { this.stopped++; }, addEventListener() {} });
const makeStream = track => ({ getTracks: () => [track], getVideoTracks: () => [track] });
const outcomeOf = request => request.then(() => "resolved", failure => failure.message);
(async () => {
  const { CameraLayer } = await import("data:text/javascript," + encodeURIComponent(source));
  const layer = new CameraLayer(() => {});
  const firstTrack = makeTrack("USB Camera");
  const secondTrack = makeTrack("Second USB Camera");
  const secondStream = makeStream(secondTrack);
  if (scenario === "disable-while-pending") {
    const enable = outcomeOf(layer.enable("chosen-camera"));
    layer.disable();
    pendingRequests[0](makeStream(firstTrack));
    console.log(JSON.stringify({ enable: await enable, active: layer.active, stopped: firstTrack.stopped }));
  } else if (scenario === "disable-while-enumerating") {
    const enable = outcomeOf(layer.enablePreferred());
    layer.disable();
    pendingEnumerations[0]([{ kind: "videoinput", label: "USB Camera", deviceId: "usb" }]);
    console.log(JSON.stringify({ enable: await enable, active: layer.active, cameraRequests: pendingRequests.length }));
  } else {
    const first = outcomeOf(layer.enable("first-camera"));
    const second = outcomeOf(layer.enable("second-camera"));
    pendingRequests[0](makeStream(firstTrack));
    pendingRequests[1](secondStream);
    const outcomes = [await first, await second];
    console.log(JSON.stringify({ outcomes, active: layer.active, activeIsSecond: layer.phase.stream === secondStream, firstStopped: firstTrack.stopped, secondStopped: secondTrack.stopped }));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
@pytest.mark.parametrize("scenario", ["synthetic", "physical", "feedback"])
def test_camera_render_release_and_feedback_boundary(scenario):
    completed = subprocess.run(
        ["node", "-e", HARNESS, str(SOURCE), scenario],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    result = json.loads(completed.stdout)
    assert result["active"] is False
    if scenario == "synthetic":
        assert result["wasActive"] is True
        assert result["draws"] == [[1, 1, 1]]
        assert result["stopped"] == 0
    elif scenario == "physical":
        assert result["constraints"] == {
            "video": {"deviceId": {"exact": "chosen-camera"}},
            "audio": False,
        }
        assert result["draws"][0] == pytest.approx([1, 4 / 3, 1])
        assert result["stopped"] == result["ended"] == 1
    else:
        assert result["wasActive"] is False
        assert result["stopped"] == 1
        assert "physical camera" in result["error"]


def run_race_scenario(scenario):
    completed = subprocess.run(
        ["node", "-e", RACE_HARNESS, str(SOURCE), scenario],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_disable_while_an_enable_is_pending_releases_the_late_stream():
    assert run_race_scenario("disable-while-pending") == {
        "enable": "A newer camera request replaced this one",
        "active": False,
        "stopped": 1,
    }


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_an_overlapping_enable_leaves_only_the_second_stream_active():
    assert run_race_scenario("overlapping") == {
        "outcomes": ["A newer camera request replaced this one", "resolved"],
        "active": True,
        "activeIsSecond": True,
        "firstStopped": 1,
        "secondStopped": 0,
    }


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_disable_while_choosing_a_camera_never_opens_one():
    assert run_race_scenario("disable-while-enumerating") == {
        "enable": "A newer camera request replaced this one",
        "active": False,
        "cameraRequests": 0,
    }


def preferred_camera(labels):
    program = f"""
    const fs = require("node:fs");
    const source = fs.readFileSync(process.argv[1], "utf8").replace('import * as THREE from "three";', "").replace('"./camera-phase.js"', JSON.stringify(require("node:url").pathToFileURL(require("node:path").join(require("node:path").dirname(process.argv[1]), "camera-phase.js")).href));
    (async () => {{
      const {{ preferredCamera }} = await import("data:text/javascript," + encodeURIComponent(source));
      const devices = {json.dumps(labels)}.map((label) => ({{ kind: "videoinput", label }}));
      devices.push({{ kind: "audioinput", label: "USB Microphone" }});
      console.log(JSON.stringify(preferredCamera(devices)?.label ?? null));
    }})();
    """
    completed = subprocess.run(
        ["node", "-e", program, str(SOURCE)],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


def test_an_external_camera_wins_over_the_built_in_one():
    assert (
        preferred_camera(["Integrated Webcam", "Avatar Cam", "USB Camera"])
        == "USB Camera"
    )


def test_the_built_in_camera_serves_when_nothing_is_plugged_in():
    assert preferred_camera(["Avatar Cam", "Integrated Webcam"]) == "Integrated Webcam"


def test_avatar_cam_is_never_a_camera_to_show():
    assert preferred_camera(["Avatar Cam"]) is None
