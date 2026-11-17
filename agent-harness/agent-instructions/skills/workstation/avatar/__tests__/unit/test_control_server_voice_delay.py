import pytest
from control_server_node_runner import evaluate_node_json, requires_node

SEATED_REGISTRY_SOURCE = """
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
let clock = 1000;
const scheduled = [];
const runScheduled = () => {
  scheduled.sort((first, second) => first.dueTime - second.dueTime);
  for (const { deliver } of scheduled.splice(0)) deliver();
};
const registry = new ConnectedClientRegistry(
  (deliver, milliseconds) => scheduled.push({ deliver, milliseconds, dueTime: clock + milliseconds }),
  () => clock,
);
const context = {
  avatarState: new AvatarStateStore(),
  clientRegistry: registry,
  speechFloor: { currentPhase: () => "idle" },
  textToSpeechGenerator: { selectCharacter: () => {} },
};
const [renderer, viewer, stage, seat] = [1, 2, 3, 4].map(makeFakeConnection);
const send = (connection, message) =>
  routeClientMessage(JSON.stringify(message), connection, context);
const levels = (connection) =>
  connection.sent.filter((message) => message.type === "audioLevel").map((message) => message.level);
const seatAll = async () => {
  await send(renderer, { type: "identify", role: "renderer" });
  await send(viewer, { type: "identify", role: "viewer" });
  await send(stage, { type: "identify", role: "stage" });
  await send(seat, { type: "identify", role: "seat" });
};
"""


@requires_node
def test_the_mac_pages_move_their_mouth_as_late_as_the_mac_plays_the_voice():
    result = evaluate_node_json(
        SEATED_REGISTRY_SOURCE
        + """
        const result = (async () => {
          await seatAll();
          await send(seat, { type: "voiceDelay", viewer: 0.3, stage: 0.05 });
          registry.sendVoiceLevel(0.5);
          const before = [renderer, viewer, stage].map(levels);
          const waits = scheduled.map(({ milliseconds }) => milliseconds);
          runScheduled();
          return { before, waits, after: [renderer, viewer, stage].map(levels), seat: seat.sent };
        })();
        """
    )
    assert result["before"] == [[0.5], [], []]
    assert sorted(result["waits"]) == [50, 300]
    assert result["after"] == [[0.5], [0.5], [0.5]]
    assert result["seat"] == [
        {
            "type": "identifyAck",
            "role": "seat",
            "status": "connected",
            "serverVersion": "1.0.0",
        }
    ]


@requires_node
def test_a_shorter_delay_never_moves_the_mouth_out_of_order():
    result = evaluate_node_json(
        SEATED_REGISTRY_SOURCE
        + """
        const result = (async () => {
          await seatAll();
          await send(seat, { type: "voiceDelay", viewer: 0.3 });
          registry.sendVoiceLevel(0.5);
          clock += 10;
          await send(seat, { type: "voiceDelay", viewer: 0.1 });
          registry.sendVoiceLevel(0.6);
          const dueTimes = scheduled.map(({ dueTime }) => dueTime);
          runScheduled();
          return { dueTimes, viewer: levels(viewer) };
        })();
        """
    )
    assert result["dueTimes"][0] <= result["dueTimes"][-1]
    assert result["viewer"] == [0.5, 0.6]


@requires_node
def test_the_mouth_follows_the_voice_at_once_after_the_seat_leaves():
    result = evaluate_node_json(
        SEATED_REGISTRY_SOURCE
        + """
        const result = (async () => {
          await seatAll();
          await send(seat, { type: "voiceDelay", viewer: 0.3, stage: 0.3 });
          registry.forget(seat);
          registry.sendVoiceLevel(0.5);
          return { pending: scheduled.length, reached: [viewer, stage].map(levels) };
        })();
        """
    )
    assert result == {"pending": 0, "reached": [[0.5], [0.5]]}


@requires_node
def test_an_implausible_voice_delay_is_ignored():
    result = evaluate_node_json(
        SEATED_REGISTRY_SOURCE
        + """
        const result = (async () => {
          await seatAll();
          await send(seat, { type: "voiceDelay", viewer: -1, stage: 5 });
          await send(seat, { type: "voiceDelay", viewer: "late" });
          registry.sendVoiceLevel(0.5);
          return { pending: scheduled.length, reached: [viewer, stage].map(levels) };
        })();
        """
    )
    assert result == {"pending": 0, "reached": [[0.5], [0.5]]}


@requires_node
@pytest.mark.parametrize("value", [0, 0.25, 1])
def test_an_agent_voice_level_moves_the_mouth_without_an_answer(value):
    result = evaluate_node_json(
        SEATED_REGISTRY_SOURCE
        + f"""
        const result = (async () => {{
          const agent = makeFakeConnection();
          const moved = [];
          registry.sendVoiceLevel = (level) => moved.push(level);
          await send(agent, {{ type: "identify", role: "agent" }});
          const answered = agent.sent.length;
          await send(agent, {{ type: "voiceLevel", value: {value} }});
          return {{ moved, replies: agent.sent.length - answered }};
        }})();
        """
    )
    assert result == {"moved": [value], "replies": 0}


@requires_node
def test_an_agent_voice_level_reaches_the_renderer_and_the_delayed_copies():
    result = evaluate_node_json(
        SEATED_REGISTRY_SOURCE
        + """
        const result = (async () => {
          const agent = makeFakeConnection();
          await seatAll();
          await send(agent, { type: "identify", role: "agent" });
          await send(seat, { type: "voiceDelay", viewer: 0.3, stage: 0.05 });
          await send(agent, { type: "voiceLevel", value: 0.5 });
          const before = [renderer, viewer, stage].map(levels);
          runScheduled();
          return { before, after: [renderer, viewer, stage].map(levels) };
        })();
        """
    )
    assert result == {
        "before": [[0.5], [], []],
        "after": [[0.5], [0.5], [0.5]],
    }


@requires_node
@pytest.mark.parametrize("value", ["1.5", "-0.1", '"loud"', "null", "undefined"])
def test_a_voice_level_outside_zero_to_one_is_refused_and_moves_nothing(value):
    result = evaluate_node_json(
        SEATED_REGISTRY_SOURCE
        + f"""
        const result = (async () => {{
          const agent = makeFakeConnection();
          const moved = [];
          registry.sendVoiceLevel = (level) => moved.push(level);
          await send(agent, {{ type: "identify", role: "agent" }});
          await send(agent, {{ type: "voiceLevel", value: {value} }});
          return {{ moved, errors: agent.sent.filter((message) => message.type === "error") }};
        }})();
        """
    )
    assert result["moved"] == []
    assert [error["error"] for error in result["errors"]] == [
        "voiceLevel needs a value from 0 to 1"
    ]
