const WebSocket = require("ws");
const {
  MessageSocketConnectionPort,
  MessageSocketServerPort,
} = require("./message-socket-server-port");

class WebSocketMessageSocketConnection extends MessageSocketConnectionPort {
  constructor(rawWebSocket) {
    super();
    this.rawWebSocket = rawWebSocket;
  }

  sendJson(payload) {
    if (!this.isOpen()) {
      return false;
    }
    this.rawWebSocket.send(JSON.stringify(payload));
    return true;
  }

  isOpen() {
    return this.rawWebSocket.readyState === WebSocket.OPEN;
  }

  onMessage(handleMessage) {
    this.rawWebSocket.on("message", (rawMessage) =>
      handleMessage(rawMessage.toString()),
    );
  }

  onClosed(handleClose) {
    this.rawWebSocket.on("close", handleClose);
  }

  onError(handleError) {
    this.rawWebSocket.on("error", handleError);
  }

  close() {
    this.rawWebSocket.close();
  }
}

class WebSocketMessageSocketServer extends MessageSocketServerPort {
  constructor(portNumber) {
    super();
    this.webSocketServer = new WebSocket.Server({ port: portNumber });
    this.keepAliveTimer = null;
    this.respondingSockets = new WeakSet();
  }

  onConnection(handleConnection) {
    this.webSocketServer.on("connection", (rawWebSocket) => {
      this.respondingSockets.add(rawWebSocket);
      rawWebSocket.on("pong", () => this.respondingSockets.add(rawWebSocket));
      handleConnection(new WebSocketMessageSocketConnection(rawWebSocket));
    });
  }

  startKeepAlive(intervalMilliseconds) {
    this.keepAliveTimer = setInterval(() => {
      this.webSocketServer.clients.forEach((rawWebSocket) => {
        if (!this.respondingSockets.has(rawWebSocket)) {
          rawWebSocket.terminate();
          return;
        }
        this.respondingSockets.delete(rawWebSocket);
        rawWebSocket.ping();
      });
    }, intervalMilliseconds);

    this.webSocketServer.on("close", () => clearInterval(this.keepAliveTimer));
  }

  close() {
    clearInterval(this.keepAliveTimer);
    this.webSocketServer.close();
  }
}

module.exports = { WebSocketMessageSocketServer };
