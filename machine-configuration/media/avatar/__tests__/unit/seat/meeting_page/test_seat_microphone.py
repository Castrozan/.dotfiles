import json
import shutil
import subprocess
from pathlib import Path

import pytest
import seat_page
from page_devices import BUILT_IN_INPUT, device

SEAT_MICROPHONE = (
    Path(__file__).resolve().parents[4]
    / "scripts/conversation/remote_seat/page/seat-microphone.js"
)
EARBUDS = device("audioinput", "in-buds", "realme Buds Air7 (Bluetooth)")
DEFAULT_EARBUDS = device("audioinput", "default", "Default - realme Buds Air7")
DEFAULT_BUILT_IN = device(
    "audioinput", "default", "Default - MacBook Pro Microphone (Built-in)"
)

OPENING = r"""
const [modulePath, devices, defaultDevice] = process.argv.slice(1);
const opened = [];
const stopped = [];
const stream = (deviceId) => {
  const track = { stop: () => stopped.push(deviceId), getSettings: () => ({ deviceId }) };
  return { getTracks: () => [track], getAudioTracks: () => [track] };
};
const mediaDevices = {
  async getUserMedia({ audio }) {
    opened.push(audio);
    return stream(audio.deviceId ? audio.deviceId.exact : defaultDevice);
  },
  async enumerateDevices() { return JSON.parse(devices); },
};
import(modulePath).then(async ({ openMicrophone }) => {
  const microphone = await openMicrophone(mediaDevices);
  console.log(JSON.stringify({
    microphone: microphone.getAudioTracks()[0].getSettings().deviceId, opened, stopped,
  }));
});
"""


def open_with(devices, default_device):
    completed = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            OPENING,
            str(SEAT_MICROPHONE),
            json.dumps(devices),
            default_device,
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)


def test_earbuds_as_the_default_input_give_way_to_the_built_in_microphone():
    opening = open_with([DEFAULT_EARBUDS, EARBUDS, BUILT_IN_INPUT], "in-buds")
    assert opening["microphone"] == "in-1"
    assert opening["stopped"] == ["in-buds"]
    assert opening["opened"][-1]["deviceId"] == {"exact": "in-1"}
    assert opening["opened"][-1]["echoCancellation"] is True


def test_the_built_in_microphone_already_open_is_kept_without_reopening():
    opening = open_with([DEFAULT_BUILT_IN, BUILT_IN_INPUT, EARBUDS], "in-1")
    assert opening["microphone"] == "in-1"
    assert opening["stopped"] == []
    assert len(opening["opened"]) == 1


def test_a_mac_without_a_built_in_microphone_keeps_its_default_input():
    opening = open_with([DEFAULT_EARBUDS, EARBUDS], "in-buds")
    assert opening["microphone"] == "in-buds"
    assert len(opening["opened"]) == 1


def test_the_seat_page_serves_its_microphone_module(tmp_path):
    files = seat_page.seat_page_files(tmp_path)
    assert files["/seat-microphone.js"] == (
        tmp_path / "seat-microphone.js",
        seat_page.JAVASCRIPT,
    )
