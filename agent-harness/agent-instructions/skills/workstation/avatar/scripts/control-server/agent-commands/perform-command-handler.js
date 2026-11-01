const {
  sendError,
  sendResponse,
} = require("../messaging/client-response-sender");

function handlePerformCommand(command, connection, context) {
  const { action, name, id } = command;
  if (!context.clientRegistry.sendToRenderer({ type: "perform", action, name, id })) {
    sendError(connection, "No renderer is connected");
    return;
  }
  sendResponse(connection, { type: "performanceRequested", action, name, id });
}

module.exports = { handlePerformCommand };
