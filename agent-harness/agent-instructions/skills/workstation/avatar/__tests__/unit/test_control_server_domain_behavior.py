from control_server_node_runner import evaluate_node_json, requires_node

FAKE_CONNECTION_SOURCE = """
const makeFakeConnection = () => {
  const sent = [];
  return {
    sent,
    closed: false,
    sendJson(payload) { sent.push(payload); return true; },
    isOpen() { return true; },
    close() { this.closed = true; },
    onMessage() {},
    onClosed() {},
    onError() {},
  };
};
"""


@requires_node
def test_speech_timing_parser_splits_a_subtitle_block_into_word_timings():
    result = evaluate_node_json(
        """
        const { parseSpeechTiming } = require("./speech/speech-timing-parser");
        const subtitles = [
          "1",
          "00:00:00,000 --> 00:00:02,000",
          "hello there",
        ].join("\\n");
        const result = parseSpeechTiming(subtitles);
        """
    )
    assert [entry["text"] for entry in result] == ["hello", "there"]
    assert [entry["phoneme"] for entry in result] == ["e", "e"]
    assert result[0]["start"] == 0.0
    assert result[1]["end"] == 2.0


@requires_node
def test_speech_timing_parser_returns_empty_for_unparseable_input():
    result = evaluate_node_json(
        """
        const { parseSpeechTiming } = require("./speech/speech-timing-parser");
        const result = parseSpeechTiming("not a subtitle file at all");
        """
    )
    assert result == []


@requires_node
def test_avatar_state_store_only_returns_to_idle_while_still_speaking():
    result = evaluate_node_json(
        """
        const { AvatarStateStore } = require("./avatar-session/avatar-state-store");
        const store = new AvatarStateStore();
        store.beginSpeaking("happy");
        const startedSpeaking = store.speaking;
        const firstReturn = store.finishSpeakingIfStillSpeaking();
        const secondReturn = store.finishSpeakingIfStillSpeaking();
        const result = {
          startedSpeaking,
          expression: store.currentExpression,
          firstReturn,
          secondReturn,
          finalState: store.current,
        };
        """
    )
    assert result == {
        "startedSpeaking": True,
        "expression": "happy",
        "firstReturn": True,
        "secondReturn": False,
        "finalState": "idle",
    }


@requires_node
def test_forgetting_a_replaced_renderer_does_not_drop_the_live_one():
    result = evaluate_node_json(
        FAKE_CONNECTION_SOURCE
        + """
        const {
          ConnectedClientRegistry,
        } = require("./avatar-session/connected-client-registry");
        const registry = new ConnectedClientRegistry();
        const firstRenderer = makeFakeConnection();
        const secondRenderer = makeFakeConnection();

        registry.registerRenderer(firstRenderer);
        registry.registerRenderer(secondRenderer);
        registry.forget(firstRenderer);

        registry.sendToRenderer({ type: "setIdle", mode: "breathing" });
        const result = {
          stillHasRenderer: registry.hasRenderer(),
          firstRendererClosed: firstRenderer.closed,
          secondRendererReceived: secondRenderer.sent.length,
          summary: registry.connectionSummary(),
        };
        """
    )
    assert result["stillHasRenderer"] is True
    assert result["firstRendererClosed"] is False
    assert result["secondRendererReceived"] == 1
    assert result["summary"] == {"agentConnected": False, "rendererConnected": True}


@requires_node
def test_agent_command_router_reports_unknown_command_types():
    result = evaluate_node_json(
        FAKE_CONNECTION_SOURCE
        + """
        const { routeAgentCommand } = require("./agent-commands/agent-command-router");
        const {
          AvatarStateStore,
        } = require("./avatar-session/avatar-state-store");
        const {
          ConnectedClientRegistry,
        } = require("./avatar-session/connected-client-registry");
        const connection = makeFakeConnection();
        const context = {
          avatarState: new AvatarStateStore(),
          clientRegistry: new ConnectedClientRegistry(),
          textToSpeechGenerator: null,
          speakerSinkName: "default",
        };
        const result = routeAgentCommand(
          JSON.stringify({ type: "danceWildly" }),
          connection,
          context,
        ).then(() => connection.sent);
        """
    )
    assert len(result) == 1
    assert result[0]["type"] == "error"
    assert "danceWildly" in result[0]["error"]


@requires_node
def test_get_status_reports_live_connection_summary():
    result = evaluate_node_json(
        FAKE_CONNECTION_SOURCE
        + """
        const {
          handleGetStatusCommand,
        } = require("./agent-commands/get-status-command-handler");
        const {
          AvatarStateStore,
        } = require("./avatar-session/avatar-state-store");
        const {
          ConnectedClientRegistry,
        } = require("./avatar-session/connected-client-registry");
        const connection = makeFakeConnection();
        const clientRegistry = new ConnectedClientRegistry();
        clientRegistry.registerAgent(connection);
        const avatarState = new AvatarStateStore();
        avatarState.applyIdleMode("floating");
        const result = handleGetStatusCommand({}, connection, {
          avatarState,
          clientRegistry,
        }).then(() => connection.sent[0]);
        """
    )
    assert result["type"] == "status"
    assert result["state"] == "idle"
    assert result["currentIdleMode"] == "floating"
    assert result["agentConnected"] is True
    assert result["rendererConnected"] is False
