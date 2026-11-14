import shutil

import pytest

from renderer_module_runner import run_renderer_module

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)

CONTROLS_UNDER_TEST = """
globalThis.window = { avatarStatus: {} };
globalThis.WebSocket = class {
  constructor() { this.sent = []; }
  send(value) { this.sent.push(JSON.parse(value)); }
};
let active = false;
const controls = new rendererModule.RendererControls({}, {
  cameras: async () => [{ deviceId: "desk", label: "Desk camera" }],
  enableCamera: async (deviceId) => {
    if (deviceId === "gone") throw new Error("Requested device not found");
    active = true;
  },
  disableCamera: () => { active = false; },
  cameraActive: () => active,
}, "stage");
controls.connect();
"""


def answers_to(messages):
    dispatches = "\n".join(
        f"await controls.dispatch({message});" for message in messages
    )
    return run_renderer_module(
        "renderer-controls.js",
        f"{CONTROLS_UNDER_TEST}{dispatches}\n"
        "console.log(JSON.stringify(controls.socket.sent));",
    )


def test_the_camera_owner_lists_its_cameras_to_whoever_asked():
    assert answers_to(['{ type: "listCameras", id: "list" }']) == [
        {
            "type": "cameraList",
            "cameras": [{"deviceId": "desk", "label": "Desk camera"}],
            "id": "list",
        }
    ]


@pytest.mark.parametrize(
    ("request_message", "message"),
    [
        ('{ type: "enableCamera", deviceId: "desk", id: "choice" }', "Camera enabled"),
        ('{ type: "disableCamera", id: "choice" }', "Camera released"),
        (
            '{ type: "enableCamera", deviceId: "gone", id: "choice" }',
            "Requested device not found",
        ),
    ],
)
def test_a_camera_choice_answers_with_its_outcome(request_message, message):
    assert answers_to([request_message]) == [
        {"type": "cameraResult", "message": message, "id": "choice"}
    ]

