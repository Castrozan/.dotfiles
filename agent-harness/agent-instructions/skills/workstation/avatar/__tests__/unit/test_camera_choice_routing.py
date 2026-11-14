import pytest
from control_server_node_runner import evaluate_node_json, requires_node

ROOM = """
const makeFakeConnection = () => {
  const sent = [];
  return { sent, sendJson(payload) { sent.push(payload); return true; }, close() {} };
};
const {
  routeClientMessage,
} = require("./avatar-session/client-connection-router");
const { AvatarStateStore } = require("./avatar-session/avatar-state-store");
const {
  ConnectedClientRegistry,
} = require("./avatar-session/connected-client-registry");
const context = {
  avatarState: new AvatarStateStore(),
  clientRegistry: new ConnectedClientRegistry(),
  speechFloor: { currentPhase: () => "idle" },
  textToSpeechGenerator: { selectCharacter: () => {} },
};
const [agent, bystander, renderer, viewer, stage] = [1, 2, 3, 4, 5].map(makeFakeConnection);
const send = (connection, message) =>
  routeClientMessage(JSON.stringify(message), connection, context);
const cameraMessages = (connection) =>
  connection.sent.filter((message) => /amera/.test(message.type));
const enter = async (...roles) => {
  for (const [connection, role] of roles)
    await send(connection, { type: "identify", role });
};
"""

CAMERA_CHOICES = [
    {"type": "listCameras", "id": "1"},
    {"type": "enableCamera", "deviceId": "desk", "id": "2"},
    {"type": "disableCamera", "id": "3"},
]


@requires_node
@pytest.mark.parametrize("choice", CAMERA_CHOICES)
def test_a_camera_choice_reaches_the_stage_alone_while_it_is_connected(choice):
    result = evaluate_node_json(
        ROOM
        + f"""
        const result = (async () => {{
          await enter([agent, "agent"], [renderer, "renderer"], [viewer, "viewer"], [stage, "stage"]);
          await send(agent, {choice!r});
          return [stage, renderer, viewer].map(cameraMessages);
        }})();
        """.replace("'", '"')
    )
    assert result == [[choice], [], []]


@requires_node
@pytest.mark.parametrize("choice", CAMERA_CHOICES)
def test_a_camera_choice_reaches_the_renderer_when_no_stage_is_connected(choice):
    result = evaluate_node_json(
        ROOM
        + f"""
        const result = (async () => {{
          await enter([agent, "agent"], [renderer, "renderer"]);
          await send(agent, {choice!r});
          return cameraMessages(renderer);
        }})();
        """.replace("'", '"')
    )
    assert result == [choice]


@requires_node
@pytest.mark.parametrize("owner", ["stage", "renderer"])
def test_the_camera_owner_answers_every_agent(owner):
    result = evaluate_node_json(
        ROOM
        + f"""
        const result = (async () => {{
          await enter([agent, "agent"], [bystander, "agent"], [{owner}, "{owner}"]);
          await send({owner}, {{ type: "cameraList", cameras: [], id: "1" }});
          await send({owner}, {{ type: "cameraResult", message: "Camera enabled", id: "2" }});
          return [agent, bystander].map((connection) =>
            cameraMessages(connection).map((message) => message.id));
        }})();
        """
    )
    assert result == [["1", "2"], ["1", "2"]]


@requires_node
def test_a_camera_choice_without_any_camera_owner_fails_for_the_asker():
    result = evaluate_node_json(
        ROOM
        + """
        const result = (async () => {
          await enter([agent, "agent"]);
          await send(agent, { type: "listCameras", id: "1" });
          return agent.sent.at(-1).error;
        })();
        """
    )
    assert result == "No renderer is connected"


@requires_node
def test_a_viewer_cannot_answer_for_the_camera():
    result = evaluate_node_json(
        ROOM
        + """
        const result = (async () => {
          await enter([agent, "agent"], [viewer, "viewer"]);
          await send(viewer, { type: "cameraResult", message: "Camera enabled", id: "1" });
          return cameraMessages(agent);
        })();
        """
    )
    assert result == []
