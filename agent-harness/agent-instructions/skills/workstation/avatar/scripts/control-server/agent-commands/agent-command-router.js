const { sendError } = require("../messaging/client-response-sender");
const { handleSpeakCommand } = require("./speak-command-handler");
const {
  handleSetExpressionCommand,
} = require("./set-expression-command-handler");
const { handleSetIdleCommand } = require("./set-idle-command-handler");
const { handleGetStatusCommand } = require("./get-status-command-handler");

const COMMAND_HANDLERS_BY_TYPE = {
  speak: handleSpeakCommand,
  setExpression: handleSetExpressionCommand,
  setIdle: handleSetIdleCommand,
  getStatus: handleGetStatusCommand,
};

async function routeAgentCommand(rawMessage, connection, context) {
  try {
    const command = JSON.parse(rawMessage);
    console.log(`📥 Agent command: ${command.type}`);

    const handler = COMMAND_HANDLERS_BY_TYPE[command.type];
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
