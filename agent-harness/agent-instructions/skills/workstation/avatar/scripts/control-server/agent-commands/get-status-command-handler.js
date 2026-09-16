const { sendResponse } = require("../messaging/client-response-sender");

async function handleGetStatusCommand(command, connection, context) {
  const { avatarState, clientRegistry } = context;

  sendResponse(connection, {
    type: "status",
    state: avatarState.current,
    currentExpression: avatarState.currentExpression,
    currentIdleMode: avatarState.currentIdleMode,
    intensity: avatarState.intensity,
    speaking: avatarState.speaking,
    uptime: avatarState.uptimeSeconds(),
    ...clientRegistry.connectionSummary(),
    timestamp: Date.now(),
  });
  console.log("📤 Sent status to agent");
}

module.exports = { handleGetStatusCommand };
