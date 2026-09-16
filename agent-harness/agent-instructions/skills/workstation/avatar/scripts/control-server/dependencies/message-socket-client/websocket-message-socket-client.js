const WebSocket = require("ws");
const { MessageSocketClientPort } = require("./message-socket-client-port");

class WebSocketMessageSocketClient extends MessageSocketClientPort {
  constructor(socketUrl) {
    super();
    this.rawWebSocket = new WebSocket(socketUrl);
  }

  onOpen(handleOpen) {
    this.rawWebSocket.on("open", handleOpen);
  }

  onMessage(handleMessage) {
    const messageListener = (rawMessage) =>
      handleMessage(rawMessage.toString());
    this.rawWebSocket.on("message", messageListener);
    return () => this.rawWebSocket.removeListener("message", messageListener);
  }

  onClosed(handleClose) {
    this.rawWebSocket.on("close", handleClose);
  }

  onError(handleError) {
    this.rawWebSocket.on("error", handleError);
  }

  sendJson(payload) {
    this.rawWebSocket.send(JSON.stringify(payload));
  }

  close() {
    this.rawWebSocket.close();
  }
}

module.exports = { WebSocketMessageSocketClient };
