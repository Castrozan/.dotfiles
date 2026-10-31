const {
  sendError,
  sendResponse,
} = require("../messaging/client-response-sender");

function handleSetVideoModeCommand(command, connection, context) {
  if (!["avatar", "camera", "composite"].includes(command.mode)) {
    sendError(connection, "Video mode must be avatar, camera, or composite");
    return;
  }
  if (
    !context.clientRegistry.sendToRenderer({
      type: "setVideoMode",
      mode: command.mode,
      id: command.id,
    })
  ) {
    sendError(connection, "No renderer is connected");
    return;
  }
  sendResponse(connection, {
    type: "videoModeRequested",
    mode: command.mode,
    id: command.id,
  });
}

module.exports = { handleSetVideoModeCommand };
