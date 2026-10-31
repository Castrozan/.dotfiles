import json
import shutil
import subprocess
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[2] / "renderer/camera-layer.js"

HARNESS = r"""
const fs = require("node:fs");
const scenario = process.argv[2];
class Scene { add(plane) { this.plane = plane; } }
class Camera { constructor() { this.position = {}; } }
class Material {}
class Geometry {}
class Mesh { constructor() { this.scale = { set: (...values) => { this.scales = values; } }; } }
class Texture { dispose() {} }
globalThis.avatarTestThree = { Scene, OrthographicCamera: Camera, MeshBasicMaterial: Material, PlaneGeometry: Geometry, Mesh, VideoTexture: Texture, CanvasTexture: Texture, sRGBEncoding: 3001 };
const drawing = { fillRect() {}, fillText() {} };
globalThis.document = { createElement: () => ({ videoWidth: 640, videoHeight: 480, play: async () => {}, getContext: () => drawing }) };
const track = { label: scenario === "feedback" ? "Avatar Cam" : "USB Camera", stopped: 0, stop() { this.stopped++; }, addEventListener(name, callback) { this[name] = callback; } };
const stream = { getTracks: () => [track], getVideoTracks: () => [track] };
let constraints;
Object.defineProperty(globalThis, "navigator", { value: { mediaDevices: { getUserMedia: async value => { constraints = value; return stream; } } } });
const source = fs.readFileSync(process.argv[1], "utf8").replace('import * as THREE from "three";', "const THREE = globalThis.avatarTestThree;");
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


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
@pytest.mark.parametrize("scenario", ["synthetic", "physical", "feedback"])
def test_camera_render_release_and_feedback_boundary(scenario):
    completed = subprocess.run(
        ["node", "-e", HARNESS, str(SOURCE), scenario],
        capture_output=True,
        text=True,
        check=True,
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
