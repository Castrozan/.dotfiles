const { sendError } = require("../messaging/client-response-sender");

const CAMERA_CHOICE_COMMANDS = ["listCameras", "enableCamera", "disableCamera"];

function handleCameraChoiceCommand(command, connection, context) {
  const { type, deviceId, id } = command;
  if (!context.clientRegistry.sendToCameraOwner({ type, deviceId, id })) {
    sendError(connection, "No renderer is connected");
  }
}

module.exports = { CAMERA_CHOICE_COMMANDS, handleCameraChoiceCommand };
