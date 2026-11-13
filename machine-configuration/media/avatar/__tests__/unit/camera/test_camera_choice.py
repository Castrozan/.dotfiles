import json
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[3] / "renderer/camera-layer.js"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)


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


@pytest.mark.parametrize(
    "built_in",
    [
        "Câmera do MacBook Air (0000:0001)",
        "FaceTime HD Camera (Built-in)",
        "MacBook Pro Camera",
    ],
)
def test_on_a_mac_an_external_camera_wins_over_the_built_in_one(built_in):
    cameras = ["OBS Virtual Camera", built_in, "Câmera USB (5258:4a55)"]
    assert preferred_camera(cameras) == "Câmera USB (5258:4a55)"
    assert preferred_camera(cameras[:2]) == built_in


def test_the_camera_that_carries_the_call_picture_is_never_a_camera_to_show():
    assert preferred_camera(["OBS Virtual Camera"]) is None
