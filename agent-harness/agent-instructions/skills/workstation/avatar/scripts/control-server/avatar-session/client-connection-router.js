const { routeAgentCommand } = require("../agent-commands/agent-command-router");
const {
  sendResponse,
  sendError,
} = require("../messaging/client-response-sender");

const SERVER_VERSION = "1.0.0";
const DISPLAY_COPY_REGISTRATIONS = {
  viewer: "registerViewer",
  stage: "registerStage",
};
const CAMERA_OWNER_EVENTS = ["videoModeChanged", "videoModeError"];

function acknowledgeIdentification(connection, role) {
  sendResponse(connection, {
    type: "identifyAck",
    role,
    status: "connected",
    serverVersion: SERVER_VERSION,
  });
}

function sendInitialStateToRenderer(connection, context) {
  const { avatarState, speechFloor } = context;
  sendResponse(connection, {
    type: "initialState",
    state: speechFloor.currentPhase(),
    expression: avatarState.currentExpression,
    idleMode: avatarState.currentIdleMode,
    intensity: avatarState.intensity,
  });
}

function showCurrentCharacterToViewer(connection, context) {
  const name = context.avatarState.currentCharacter;
  if (name) {
    sendResponse(connection, { type: "setCharacter", name });
  }
}

function handleIdentification(role, connection, context) {
  const { clientRegistry } = context;

  if (role === "agent") {
    clientRegistry.registerAgent(connection);
    acknowledgeIdentification(connection, "agent");
    return;
  }

  if (role === "renderer") {
    clientRegistry.registerRenderer(connection);
    acknowledgeIdentification(connection, "renderer");
    sendInitialStateToRenderer(connection, context);
    return;
  }

  if (Object.hasOwn(DISPLAY_COPY_REGISTRATIONS, role)) {
    clientRegistry[DISPLAY_COPY_REGISTRATIONS[role]](connection);
    acknowledgeIdentification(connection, role);
    sendInitialStateToRenderer(connection, context);
    showCurrentCharacterToViewer(connection, context);
    return;
  }

  sendError(connection, `Unknown role: ${role}`);
  connection.close();
}

function handleRendererEvent(event, context) {
  console.log("📥 Renderer event:", event.type);
  if (
    [
      "videoModeChanged",
      "videoModeError",
      "performanceApplied",
      "performanceError",
      "characterChanged",
      "characterError",
    ].includes(event.type)
  ) {
    context.clientRegistry.sendToAgents(event);
  }
  if (event.type === "characterChanged") {
    context.avatarState.applyCharacter(event.name);
    context.textToSpeechGenerator.selectCharacter(event.name);
  }
  if (event.type === "speechEnd") {
    console.log("🔄 Speech ended");
  }
}

function handleStageEvent(event, context) {
  if (CAMERA_OWNER_EVENTS.includes(event.type)) {
    context.clientRegistry.sendToAgents(event);
  }
}

async function routeIdentifiedMessage(rawMessage, connection, context) {
  const { clientRegistry } = context;

  if (clientRegistry.isAgent(connection)) {
    await routeAgentCommand(rawMessage, connection, context);
    return;
  }

  if (clientRegistry.isRenderer(connection)) {
    handleRendererEvent(JSON.parse(rawMessage), context);
    return;
  }

  if (clientRegistry.isStage(connection)) {
    handleStageEvent(JSON.parse(rawMessage), context);
    return;
  }

  if (clientRegistry.isViewer(connection)) {
    return;
  }

  sendResponse(connection, {
    type: "identifyRequest",
    message:
      'Please identify with { type: "identify", role: "agent"|"renderer" }',
  });
}

async function routeClientMessage(rawMessage, connection, context) {
  try {
    const message = JSON.parse(rawMessage);
    if (message.type === "identify") {
      handleIdentification(message.role, connection, context);
      return;
    }
    await routeIdentifiedMessage(rawMessage, connection, context);
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
