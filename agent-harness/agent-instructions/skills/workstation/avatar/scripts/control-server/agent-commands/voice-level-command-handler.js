const { sendError } = require("../messaging/client-response-sender");

const MOUTH_LEVEL_REFUSAL = "voiceLevel needs a value from 0 to 1";

function handleVoiceLevelCommand({ value }, connection, context) {
  if (!Number.isFinite(value) || value < 0 || value > 1) {
    sendError(connection, MOUTH_LEVEL_REFUSAL);
    return;
  }
  context.clientRegistry.sendVoiceLevel(value);
}

module.exports = { handleVoiceLevelCommand };
