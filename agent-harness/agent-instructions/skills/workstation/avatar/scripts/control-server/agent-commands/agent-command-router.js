const { sendError } = require("../messaging/client-response-sender");
const { handleSpeakCommand } = require("./speak-command-handler");
const {
  handleSetExpressionCommand,
} = require("./set-expression-command-handler");
const { handleSetIdleCommand } = require("./set-idle-command-handler");
const {
  handleSetPresentedCommand,
} = require("./set-presented-command-handler");
const {
  handleStopSpeakingCommand,
} = require("./stop-speaking-command-handler");
const { handleGetStatusCommand } = require("./get-status-command-handler");
const { handlePerformCommand } = require("./perform-command-handler");

const {
  handleSetVideoModeCommand,
} = require("./set-video-mode-command-handler");
const {
  handleSetCharacterCommand,
} = require("./set-character-command-handler");
const {
  CAMERA_CHOICE_COMMANDS,
  handleCameraChoiceCommand,
} = require("./camera-choice-command-handler");

const COMMAND_HANDLERS_BY_TYPE = {
  speak: handleSpeakCommand,
  stopSpeaking: handleStopSpeakingCommand,
  setVideoMode: handleSetVideoModeCommand,
  setCharacter: handleSetCharacterCommand,
  setExpression: handleSetExpressionCommand,
  setIdle: handleSetIdleCommand,
  setPresented: handleSetPresentedCommand,
  getStatus: handleGetStatusCommand,
  perform: handlePerformCommand,
  ...Object.fromEntries(
    CAMERA_CHOICE_COMMANDS.map((type) => [type, handleCameraChoiceCommand]),
  ),
};

async function routeAgentCommand(rawMessage, connection, context) {
  try {
    const command = JSON.parse(rawMessage);
    console.log(`📥 Agent command: ${command.type}`);

    const handler = Object.hasOwn(COMMAND_HANDLERS_BY_TYPE, command.type)
      ? COMMAND_HANDLERS_BY_TYPE[command.type]
      : null;
    if (!handler) {
      sendError(connection, `Unknown command type: ${command.type}`);
      return;
    }

    await handler(command, connection, context);
  } catch (error) {
    console.error("❌ Error handling command:", error.message);
    sendError(connection, error.message);
  }
}

module.exports = { routeAgentCommand };
