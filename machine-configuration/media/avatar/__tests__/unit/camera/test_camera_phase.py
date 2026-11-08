import json
import shutil
import subprocess
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[3] / "renderer/camera-phase.js"

PROGRAM = r"""
const fs = require("node:fs");
const source = fs.readFileSync(process.argv[1], "utf8").replace('import * as THREE from "three";', "");
(async () => {
  const { CAMERA_PHASES, nextCameraPhase } = await import("data:text/javascript," + encodeURIComponent(source));
  const phases = {
    off: { name: CAMERA_PHASES.OFF },
    opening: { name: CAMERA_PHASES.OPENING, generation: 1 },
    live: { name: CAMERA_PHASES.LIVE, generation: 1, stream: "stream-1" },
    synthetic: { name: CAMERA_PHASES.SYNTHETIC, canvas: "canvas-1" },
  };
  const events = {
    open: { type: "open", generation: 2 },
    synthetic: { type: "synthetic", canvas: "canvas-2" },
    release: { type: "release" },
    "ready-current": { type: "ready", generation: 1, stream: "stream-2" },
    "ready-stale": { type: "ready", generation: 9, stream: "stream-2" },
  };
  const table = {};
  for (const [phaseName, phase] of Object.entries(phases)) {
    table[phaseName] = {};
    for (const [eventName, event] of Object.entries(events)) {
      const next = nextCameraPhase(phase, event);
      table[phaseName][eventName] = next === phase ? "unchanged" : next;
    }
  }
  console.log(JSON.stringify(table));
})().catch(error => { console.error(error); process.exitCode = 1; });
"""

OPENED_AT_TWO = {"name": "opening", "generation": 2}
SYNTHETIC_AT_TWO = {"name": "synthetic", "canvas": "canvas-2"}
OFF = {"name": "off"}
LIVE_FROM_OPENING = {"name": "live", "generation": 1, "stream": "stream-2"}

EXPECTED_TABLE = {
    "off": {
        "open": OPENED_AT_TWO,
        "synthetic": SYNTHETIC_AT_TWO,
        "release": OFF,
        "ready-current": "unchanged",
        "ready-stale": "unchanged",
    },
    "opening": {
        "open": OPENED_AT_TWO,
        "synthetic": SYNTHETIC_AT_TWO,
        "release": OFF,
        "ready-current": LIVE_FROM_OPENING,
        "ready-stale": "unchanged",
    },
    "live": {
        "open": OPENED_AT_TWO,
        "synthetic": SYNTHETIC_AT_TWO,
        "release": OFF,
        "ready-current": "unchanged",
        "ready-stale": "unchanged",
    },
    "synthetic": {
        "open": OPENED_AT_TWO,
        "synthetic": SYNTHETIC_AT_TWO,
        "release": OFF,
        "ready-current": "unchanged",
        "ready-stale": "unchanged",
    },
}


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_every_camera_phase_meets_every_event():
    completed = subprocess.run(
        ["node", "-e", PROGRAM, str(SOURCE)],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert json.loads(completed.stdout) == EXPECTED_TABLE
