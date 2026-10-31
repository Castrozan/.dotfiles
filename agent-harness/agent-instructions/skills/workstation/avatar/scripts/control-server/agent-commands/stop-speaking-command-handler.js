const { sendResponse } = require("../messaging/client-response-sender");

function handleStopSpeakingCommand(_command, connection, context) {
  context.speechFloor.interrupt();
  sendResponse(connection, { type: "stopSpeakingAck", status: "stopped" });
}

module.exports = { handleStopSpeakingCommand };
