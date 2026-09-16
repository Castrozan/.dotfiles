function sendResponse(connection, payload) {
  return connection ? connection.sendJson(payload) : false;
}

function sendError(connection, errorMessage) {
  return sendResponse(connection, {
    type: "error",
    error: errorMessage,
    timestamp: Date.now(),
  });
}

module.exports = { sendResponse, sendError };
