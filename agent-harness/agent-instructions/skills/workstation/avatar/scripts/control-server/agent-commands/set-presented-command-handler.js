const {
  sendResponse,
  sendError,
} = require("../messaging/client-response-sender");

async function handleSetPresentedCommand(command, connection, context) {
  const { presented } = command;
  if (!context.clientRegistry.sendToRenderer({ type: "setPresented", presented })) {
    sendError(connection, "No renderer is connected");
    return;
  }
  sendResponse(connection, { type: "presentedAck", presented });
}

module.exports = { handleSetPresentedCommand };
