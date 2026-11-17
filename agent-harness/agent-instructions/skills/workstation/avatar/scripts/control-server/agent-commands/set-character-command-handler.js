const {
  sendError,
  sendResponse,
} = require("../messaging/client-response-sender");

function answerCharacterChanged(command, connection) {
  sendResponse(connection, {
    type: "characterChanged",
    name: command.name,
    id: command.id,
  });
}

function adoptCharacterWithoutRenderer(command, connection, context) {
  const { avatarState, textToSpeechGenerator } = context;
  if (!textToSpeechGenerator.selectCharacter(command.name)) {
    sendError(connection, `Unknown character: ${command.name}`);
    return;
  }
  avatarState.applyCharacter(command.name);
  answerCharacterChanged(command, connection);
}

function handleSetCharacterCommand(command, connection, context) {
  const { avatarState, clientRegistry, textToSpeechGenerator } = context;
  if (avatarState.currentCharacter === command.name) {
    textToSpeechGenerator.selectCharacter(command.name);
    answerCharacterChanged(command, connection);
    return;
  }
  if (
    !clientRegistry.sendToRenderer({
      type: "setCharacter",
      name: command.name,
      id: command.id,
    })
  ) {
    adoptCharacterWithoutRenderer(command, connection, context);
    return;
  }
  sendResponse(connection, {
    type: "characterRequested",
    name: command.name,
    id: command.id,
  });
}

module.exports = { handleSetCharacterCommand };
