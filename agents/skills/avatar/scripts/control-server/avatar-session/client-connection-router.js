const { routeAgentCommand } = require("../agent-commands/agent-command-router");
const {
  sendResponse,
  sendError,
} = require("../messaging/client-response-sender");

const SERVER_VERSION = "1.0.0";

function acknowledgeIdentification(connection, role) {
  sendResponse(connection, {
    type: "identifyAck",
    role,
    status: "connected",
    serverVersion: SERVER_VERSION,
  });
}

function sendInitialStateToRenderer(connection, avatarState) {
  sendResponse(connection, {
    type: "initialState",
    state: avatarState.current,
    expression: avatarState.currentExpression,
    idleMode: avatarState.currentIdleMode,
    intensity: avatarState.intensity,
  });
}

function handleIdentification(role, connection, context) {
  const { avatarState, clientRegistry } = context;

  if (role === "agent") {
    clientRegistry.registerAgent(connection);
    acknowledgeIdentification(connection, "agent");
    return;
  }

  if (role === "renderer") {
    clientRegistry.registerRenderer(connection);
    acknowledgeIdentification(connection, "renderer");
    sendInitialStateToRenderer(connection, avatarState);
    return;
  }

  sendError(connection, `Unknown role: ${role}`);
  connection.close();
}

function handleRendererEvent(event, context) {
  console.log("📥 Renderer event:", event.type);
  if (event.type === "speechEnd") {
    context.avatarState.finishSpeaking();
    console.log("🔄 Speech ended, transitioned to IDLE");
  }
}

async function routeClientMessage(rawMessage, connection, context) {
  try {
    const message = JSON.parse(rawMessage);
    const { clientRegistry } = context;

    if (message.type === "identify") {
      handleIdentification(message.role, connection, context);
      return;
    }

    if (clientRegistry.isAgent(connection)) {
      await routeAgentCommand(rawMessage, connection, context);
      return;
    }

    if (clientRegistry.isRenderer(connection)) {
      handleRendererEvent(message, context);
      return;
    }

    sendResponse(connection, {
      type: "identifyRequest",
      message:
        'Please identify with { type: "identify", role: "agent"|"renderer" }',
    });
  } catch (error) {
    console.error("❌ Error processing message:", error.message);
    sendError(connection, `Message processing error: ${error.message}`);
  }
}

function attachClientConnection(connection, context) {
  console.log("🔌 New WebSocket connection");
  connection.onMessage((rawMessage) =>
    routeClientMessage(rawMessage, connection, context),
  );
  connection.onClosed(() => context.clientRegistry.forget(connection));
  connection.onError((error) =>
    console.error("❌ WebSocket error:", error.message),
  );
}

module.exports = { attachClientConnection, routeClientMessage };
