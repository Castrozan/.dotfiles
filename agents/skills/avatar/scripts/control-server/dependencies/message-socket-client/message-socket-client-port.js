const notImplemented = (methodName) => {
  throw new Error(
    `MessageSocketClientPort.${methodName} must be implemented by an adapter`,
  );
};

class MessageSocketClientPort {
  onOpen(handleOpen) {
    notImplemented("onOpen");
  }

  onMessage(handleMessage) {
    notImplemented("onMessage");
  }

  onClosed(handleClose) {
    notImplemented("onClosed");
  }

  onError(handleError) {
    notImplemented("onError");
  }

  sendJson(payload) {
    notImplemented("sendJson");
  }

  close() {
    notImplemented("close");
  }
}

module.exports = { MessageSocketClientPort };
