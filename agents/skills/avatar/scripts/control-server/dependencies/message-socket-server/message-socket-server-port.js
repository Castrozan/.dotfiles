const notImplemented = (className, methodName) => {
  throw new Error(
    `${className}.${methodName} must be implemented by an adapter`,
  );
};

class MessageSocketConnectionPort {
  sendJson(payload) {
    notImplemented("MessageSocketConnectionPort", "sendJson");
  }

  isOpen() {
    notImplemented("MessageSocketConnectionPort", "isOpen");
  }

  onMessage(handleMessage) {
    notImplemented("MessageSocketConnectionPort", "onMessage");
  }

  onClosed(handleClose) {
    notImplemented("MessageSocketConnectionPort", "onClosed");
  }

  onError(handleError) {
    notImplemented("MessageSocketConnectionPort", "onError");
  }

  close() {
    notImplemented("MessageSocketConnectionPort", "close");
  }
}

class MessageSocketServerPort {
  onConnection(handleConnection) {
    notImplemented("MessageSocketServerPort", "onConnection");
  }

  startKeepAlive(intervalMilliseconds) {
    notImplemented("MessageSocketServerPort", "startKeepAlive");
  }

  close() {
    notImplemented("MessageSocketServerPort", "close");
  }
}

module.exports = { MessageSocketConnectionPort, MessageSocketServerPort };
