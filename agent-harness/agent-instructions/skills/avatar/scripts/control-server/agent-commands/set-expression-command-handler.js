const {
  sendResponse,
  sendError,
} = require("../messaging/client-response-sender");

async function handleSetExpressionCommand(command, connection, context) {
  const { name, intensity = 1.0, duration = 2000 } = command;

  if (!name) {
    sendError(connection, "Missing required field: name");
    return;
  }

  const { avatarState, clientRegistry } = context;
  avatarState.applyExpression(name, intensity);

  if (clientRegistry.hasRenderer()) {
    clientRegistry.sendToRenderer({
      type: "updateExpression",
      expression: name,
      intensity,
      transitionMs: duration,
    });
    console.log(
      `📤 Forwarded to renderer: updateExpression (${name}, ${intensity})`,
    );
  }

  sendResponse(connection, {
    type: "expressionAck",
    expression: name,
    intensity,
    status: "updated",
  });
}

module.exports = { handleSetExpressionCommand };
