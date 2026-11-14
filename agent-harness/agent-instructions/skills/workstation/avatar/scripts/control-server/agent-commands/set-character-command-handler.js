const {
  sendError,
  sendResponse,
} = require("../messaging/client-response-sender");

function handleSetCharacterCommand(command, connection, context) {
  const { avatarState, clientRegistry, textToSpeechGenerator } = context;
  if (avatarState.currentCharacter === command.name) {
    textToSpeechGenerator.selectCharacter(command.name);
    sendResponse(connection, {
      type: "characterChanged",
      name: command.name,
      id: command.id,
    });
    return;
  }
  if (
    !clientRegistry.sendToRenderer({
      type: "setCharacter",
      name: command.name,
      id: command.id,
    })
  ) {
    sendError(connection, "No renderer is connected");
    return;
  }
  textToSpeechGenerator.selectCharacter(command.name);
  sendResponse(connection, {
    type: "characterRequested",
    name: command.name,
    id: command.id,
  });
}

module.exports = { handleSetCharacterCommand };
