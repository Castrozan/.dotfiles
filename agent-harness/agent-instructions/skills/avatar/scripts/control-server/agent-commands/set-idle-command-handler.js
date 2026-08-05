const { sendResponse } = require("../messaging/client-response-sender");

async function handleSetIdleCommand(command, connection, context) {
  const { mode = "breathing" } = command;
  const { avatarState, clientRegistry } = context;

  avatarState.applyIdleMode(mode);

  if (clientRegistry.hasRenderer()) {
    clientRegistry.sendToRenderer({ type: "setIdle", mode });
    console.log(`📤 Forwarded to renderer: setIdle (${mode})`);
  }

  sendResponse(connection, {
    type: "idleAck",
    mode,
    status: "updated",
  });
}

module.exports = { handleSetIdleCommand };
