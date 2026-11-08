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
def test_speech_leaves_the_avatar_expression_alone():
    result = evaluate_node_json(
        """
        const childProcess = require("child_process");
        childProcess.spawn = () => ({
          stderr: { on: () => {} },
          on: (event, resolve) => event === "close" && resolve(),
          kill: () => {},
        });
        const { AvatarStateStore } = require("./avatar-session/avatar-state-store");
        const { handleSpeakCommand } = require("./agent-commands/speak-command-handler");
        const avatarState = new AvatarStateStore();
        avatarState.applyExpression("surprised", 0.8);
        const context = {
          avatarState,
          clientRegistry: { hasRenderer: () => false, sendToRenderer: () => {} },
          speakerSinkName: "default",
          textToSpeechGenerator: {
            generate: async () => ({ audioPath: "/a.wav", source: "local" }),
          },
          speechFloor: {
            enqueue: async (_, perform) => {
              await (await perform(() => true)).finished;
              return { status: "finished" };
            },
          },
        };
        const result = handleSpeakCommand(
          { text: "oi", emotion: "happy", output: "speakers", id: "turn" },
          { sendJson: () => {} },
          context,
        ).then(() => ({
          expression: avatarState.currentExpression,
          intensity: avatarState.intensity,
        }));
        """
    )
    assert result == {"expression": "surprised", "intensity": 0.8}


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
        const speechFloor = { currentPhase: () => "playing" };
        const result = handleGetStatusCommand({}, connection, {
          avatarState,
          clientRegistry,
          speechFloor,
        }).then(() => connection.sent[0]);
        """
    )
    assert result["type"] == "status"
    assert result["state"] == "playing"
    assert result["speaking"] is True
    assert result["currentIdleMode"] == "floating"
    assert result["agentConnected"] is True
    assert result["rendererConnected"] is False
