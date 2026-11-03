const {
  sendError,
  sendResponse,
} = require("../messaging/client-response-sender");

function handleSetCharacterCommand(command, connection, context) {
  if (
    !context.clientRegistry.sendToRenderer({
      type: "setCharacter",
      name: command.name,
      id: command.id,
    })
  ) {
    sendError(connection, "No renderer is connected");
    return;
  }
  sendResponse(connection, {
    type: "characterRequested",
    name: command.name,
    id: command.id,
  });
}

module.exports = { handleSetCharacterCommand };
