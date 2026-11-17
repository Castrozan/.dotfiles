from control_server_node_runner import evaluate_node_json, requires_node
from character_voice_fixtures import (
    CHARACTER_VOICED_GENERATOR,
    CHARACTER_REQUEST_SESSION,
)

RENDERER_ARRIVES_LATER = """
const { routeClientMessage } = require("./avatar-session/client-connection-router");
const {
  ConnectedClientRegistry,
} = require("./avatar-session/connected-client-registry");
context.clientRegistry = new ConnectedClientRegistry();
context.speechFloor = { currentPhase: () => "idle" };
const renderer = { sent: [], sendJson(value) { this.sent.push(value); return true; }, close() {} };
const rendererSays = (message) =>
  routeClientMessage(JSON.stringify(message), renderer, context);
"""


@requires_node
def test_without_a_renderer_the_server_adopts_the_character_and_its_voice():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + """
        rendererConnected.value = false;
        request("second", "request-1");
        const result = {
          voice: spokenVoice(),
          recorded: avatarState.currentCharacter,
          replies: sent.map((reply) => [reply.type, reply.name, reply.id]),
        };
        """
    )
    assert result == {
        "voice": "secondCloud",
        "recorded": "second",
        "replies": [["characterChanged", "second", "request-1"]],
    }


@requires_node
def test_without_a_renderer_an_unknown_character_is_refused_and_not_recorded():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + """
        rendererConnected.value = false;
        request("nobody", "request-2");
        const result = {
          voice: spokenVoice(),
          recorded: avatarState.currentCharacter,
          reply: sent[0].error,
        };
        """
    )
    assert result == {
        "voice": "firstCloud",
        "recorded": None,
        "reply": "Unknown character: nobody",
    }


@requires_node
def test_with_a_renderer_the_character_is_requested_and_not_adopted_early():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + """
        request("second", "request-3");
        const result = {
          voice: spokenVoice(),
          recorded: avatarState.currentCharacter,
          forwarded: forwarded.length,
          replies: sent.map((reply) => reply.type),
        };
        """
    )
    assert result == {
        "voice": "firstCloud",
        "recorded": None,
        "forwarded": 1,
        "replies": ["characterRequested"],
    }


@requires_node
def test_a_renderer_arriving_later_is_shown_the_adopted_character():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + RENDERER_ARRIVES_LATER
        + """
        const result = (async () => {
          request("second", "request-4");
          await rendererSays({ type: "identify", role: "renderer" });
          await rendererSays({ type: "characterChanged", name: "second" });
          return {
            shown: renderer.sent.map((message) => [message.type, message.name]),
            recorded: avatarState.currentCharacter,
            voice: spokenVoice(),
          };
        })();
        """
    )
    assert result["shown"] == [
        ["identifyAck", None],
        ["initialState", None],
        ["setCharacter", "second"],
    ]
    assert result["recorded"] == "second"
    assert result["voice"] == "secondCloud"


@requires_node
def test_a_renderer_arriving_without_an_adopted_character_is_told_none():
    result = evaluate_node_json(
        CHARACTER_VOICED_GENERATOR
        + CHARACTER_REQUEST_SESSION
        + RENDERER_ARRIVES_LATER
        + """
        const result = (async () => {
          await rendererSays({ type: "identify", role: "renderer" });
          return renderer.sent.map((message) => message.type);
        })();
        """
    )
    assert result == ["identifyAck", "initialState"]
