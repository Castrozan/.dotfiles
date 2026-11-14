import json
import shutil
import subprocess
from pathlib import Path

import pytest

CONTROLS_PAGE = Path(__file__).resolve().parents[3] / "renderer/controls.js"

PAGE = r"""
const fs = require("node:fs");
const element = () => ({ textContent: "", value: "", options: [],
  replaceChildren(...options) { this.options = options; } });
const elements = { "#status": element(), "#devices": element(),
  "#enable": element(), "#disable": element() };
const modes = ["avatar", "camera"].map((mode) => ({ dataset: { mode } }));
globalThis.Option = class { constructor(label, value) { this.label = label; this.value = value; } };
globalThis.document = {
  querySelector: (selector) => elements[selector],
  querySelectorAll: () => modes,
};
let socket;
globalThis.WebSocket = class {
  constructor(url) { this.url = url; this.sent = []; socket = this; }
  send(value) { this.sent.push(JSON.parse(value)); }
};
const receive = (message) => socket.onmessage({ data: JSON.stringify(message) });
(async () => {
  await import("data:text/javascript," + encodeURIComponent(fs.readFileSync(process.argv[1], "utf8")));
  socket.onopen();
  receive({ type: "identifyAck" });
  receive({ type: "cameraList", cameras: [
    { deviceId: "desk", label: "Desk camera" }, { deviceId: "lid", label: "" } ] });
  elements["#devices"].value = "lid";
  elements["#enable"].onclick();
  receive({ type: "cameraResult", message: "Camera enabled" });
  const statusAfterChoice = elements["#status"].textContent;
  elements["#disable"].onclick();
  modes[1].onclick();
  receive({ type: "videoModeError", message: "No physical camera is connected" });
  console.log(JSON.stringify({
    url: socket.url,
    sent: socket.sent.map(({ id, ...message }) => message),
    identified: socket.sent.filter((message) => message.id).length,
    offered: elements["#devices"].options.map((option) => [option.label, option.value]),
    statusAfterChoice,
    status: elements["#status"].textContent,
  }));
})().catch((error) => { console.error(error); process.exitCode = 1; });
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
def test_the_controls_page_chooses_a_camera_through_the_control_server_alone():
    completed = subprocess.run(
        ["node", "-e", PAGE, str(CONTROLS_PAGE)],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    page = json.loads(completed.stdout)
    assert page["url"] == "ws://127.0.0.1:8765"
    assert page["sent"] == [
        {"type": "identify", "role": "agent"},
        {"type": "listCameras"},
        {"type": "enableCamera", "deviceId": "lid"},
        {"type": "listCameras"},
        {"type": "disableCamera"},
        {"type": "setVideoMode", "mode": "camera"},
    ]
    assert page["identified"] == 5
    assert page["offered"] == [["Desk camera", "desk"], ["Camera", "lid"]]
    assert page["statusAfterChoice"] == "Camera enabled"
    assert page["status"] == "No physical camera is connected"
    assert "BroadcastChannel" not in CONTROLS_PAGE.read_text()
