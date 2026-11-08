const { sendResponse } = require("../messaging/client-response-sender");

async function handleGetStatusCommand(command, connection, context) {
  const { avatarState, clientRegistry, speechFloor } = context;
  const state = speechFloor.currentPhase();

  sendResponse(connection, {
    type: "status",
    state,
    currentExpression: avatarState.currentExpression,
    currentIdleMode: avatarState.currentIdleMode,
    intensity: avatarState.intensity,
    speaking: state !== "idle",
    uptime: avatarState.uptimeSeconds(),
    ...clientRegistry.connectionSummary(),
    timestamp: Date.now(),
  });
  console.log("📤 Sent status to agent");
}

module.exports = { handleGetStatusCommand };
