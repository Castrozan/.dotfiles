import json
import shutil
import subprocess

import pytest

from test_camera_layer import SOURCE, STUBS

FAILURE_HARNESS = (
    STUBS
    + r"""
const scenario = process.argv[2];
const mediaDevices = scenario === "denied"
  ? { getUserMedia: () => Promise.reject(new Error("Permission denied")) }
  : { enumerateDevices: async () => [] };
Object.defineProperty(globalThis, "navigator", { value: { mediaDevices } });
(async () => {
  const { CameraLayer } = await import("data:text/javascript," + encodeURIComponent(source));
  const layer = new CameraLayer(() => {});
  const request = scenario === "denied" ? layer.enable("chosen-camera") : layer.enablePreferred();
  const outcome = await request.then(() => "resolved", (failure) => failure.message);
  console.log(JSON.stringify({ outcome, phase: layer.phase.name }));
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
@pytest.mark.parametrize(
    ("scenario", "outcome"),
    [("denied", "Permission denied"), ("no-camera", "No physical camera is connected")],
)
def test_a_failed_camera_request_leaves_the_layer_off(scenario, outcome):
    completed = subprocess.run(
        ["node", "-e", FAILURE_HARNESS, str(SOURCE), scenario],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert json.loads(completed.stdout) == {"outcome": outcome, "phase": "off"}
