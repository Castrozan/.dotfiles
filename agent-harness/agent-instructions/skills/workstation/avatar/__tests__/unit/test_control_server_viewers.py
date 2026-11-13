from control_server_node_runner import evaluate_node_json, requires_node

FAKE_CONNECTION_SOURCE = """
const makeFakeConnection = () => {
  const sent = [];
  return { sent, sendJson(payload) { sent.push(payload); return true; }, close() {} };
};
"""


@requires_node
def test_a_viewer_mirrors_the_renderer_without_speaking_for_it():
    result = evaluate_node_json(
        FAKE_CONNECTION_SOURCE
        + """
        const {
          routeClientMessage,
        } = require("./avatar-session/client-connection-router");
        const {
          AvatarStateStore,
        } = require("./avatar-session/avatar-state-store");
        const {
          ConnectedClientRegistry,
        } = require("./avatar-session/connected-client-registry");
        const selected = [];
        const context = {
          avatarState: new AvatarStateStore(),
          clientRegistry: new ConnectedClientRegistry(),
          speechFloor: { currentPhase: () => "idle" },
          textToSpeechGenerator: { selectCharacter: (name) => selected.push(name) },
        };
        const renderer = makeFakeConnection();
        const viewer = makeFakeConnection();
        const send = (connection, message) =>
          routeClientMessage(JSON.stringify(message), connection, context);
        const level = (value) => ({ type: "audioLevel", level: value });
        const result = (async () => {
          await send(renderer, { type: "identify", role: "renderer" });
          await send(renderer, { type: "characterChanged", name: "vita" });
          await send(viewer, { type: "identify", role: "viewer" });
          await send(viewer, { type: "characterChanged", name: "intruder" });
          const reached = context.clientRegistry.sendToRenderer(level(0.5));
          context.clientRegistry.forget(viewer);
          context.clientRegistry.sendToRenderer(level(0.1));
          return {
            reached,
            selected,
            viewer: viewer.sent.map((message) => [
              message.type,
              message.name ?? message.role ?? message.level,
            ]),
            rendererLevels: renderer.sent.filter(
              (message) => message.type === "audioLevel",
            ).length,
            stillRenderer: context.clientRegistry.hasRenderer(),
          };
        })();
        """
    )
    assert result["reached"] is True
    assert result["selected"] == ["vita"]
    assert result["viewer"] == [
        ["identifyAck", "viewer"],
        ["initialState", None],
        ["setCharacter", "vita"],
        ["audioLevel", 0.5],
    ]
    assert result["rendererLevels"] == 2
    assert result["stillRenderer"] is True


@requires_node
def test_the_control_socket_admits_the_renderer_and_the_remote_window_only():
    result = evaluate_node_json(
        """
        const { controlOrigins } = require("./avatar-session/page-origins");
        const result = Promise.resolve(controlOrigins("3000"));
        """
    )
    assert sorted(result) == [
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8770",
        "http://localhost:3000",
        "http://localhost:8770",
    ]


@requires_node
def test_the_stage_owns_the_camera_while_it_is_connected():
    result = evaluate_node_json(
        FAKE_CONNECTION_SOURCE
        + """
        const {
          routeClientMessage,
        } = require("./avatar-session/client-connection-router");
        const {
          AvatarStateStore,
        } = require("./avatar-session/avatar-state-store");
        const {
          ConnectedClientRegistry,
        } = require("./avatar-session/connected-client-registry");
        const {
          handleSetVideoModeCommand,
        } = require("./agent-commands/set-video-mode-command-handler");
        const context = {
          avatarState: new AvatarStateStore(),
          clientRegistry: new ConnectedClientRegistry(),
          speechFloor: { currentPhase: () => "idle" },
          textToSpeechGenerator: { selectCharacter: () => {} },
        };
        const [agent, renderer, viewer, stage] = [1, 2, 3, 4].map(makeFakeConnection);
        const send = (connection, message) =>
          routeClientMessage(JSON.stringify(message), connection, context);
        const types = (connection) => connection.sent.map((message) => message.type);
        const askForCamera = () =>
          handleSetVideoModeCommand({ mode: "camera", id: "1" }, agent, context);
        const result = (async () => {
          await send(agent, { type: "identify", role: "agent" });
          await send(renderer, { type: "identify", role: "renderer" });
          await send(viewer, { type: "identify", role: "viewer" });
          await send(stage, { type: "identify", role: "stage" });
          askForCamera();
          await send(stage, { type: "videoModeChanged", mode: "camera", id: "1" });
          await send(stage, { type: "characterChanged", name: "intruder" });
          context.clientRegistry.sendToRenderer({ type: "audioLevel", level: 0.5 });
          const whileStaged = [renderer, viewer, stage, agent].map(types);
          context.clientRegistry.forget(stage);
          askForCamera();
          return { whileStaged, rendererAfter: types(renderer), viewerAfter: types(viewer) };
        })();
        """
    )
    renderer, viewer, stage, agent = result["whileStaged"]
    assert "setVideoMode" not in renderer + viewer
    assert stage == ["identifyAck", "initialState", "setVideoMode", "audioLevel"]
    assert agent == ["identifyAck", "videoModeRequested", "videoModeChanged"]
    assert renderer[-1] == viewer[-1] == "audioLevel"
    assert result["rendererAfter"][-1] == "setVideoMode"
    assert "setVideoMode" not in result["viewerAfter"]
