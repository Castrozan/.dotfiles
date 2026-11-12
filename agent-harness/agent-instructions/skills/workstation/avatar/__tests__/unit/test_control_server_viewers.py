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
