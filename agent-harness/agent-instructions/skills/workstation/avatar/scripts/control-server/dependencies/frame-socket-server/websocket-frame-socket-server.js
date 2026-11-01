const WebSocket = require("ws");
const { FrameSocketServerPort } = require("./frame-socket-server-port");

class WebSocketFrameSocketServer extends FrameSocketServerPort {
  constructor({ portNumber, frameByteLength, allowedOrigins }) {
    super();
    this.frameByteLength = frameByteLength;
    this.webSocketServer = new WebSocket.Server({
      port: portNumber,
      host: "127.0.0.1",
      maxPayload: frameByteLength,
      verifyClient: ({ origin }) => allowedOrigins.includes(origin),
    });
  }

  onFrame(handleFrame) {
    this.webSocketServer.on("connection", (rawWebSocket) => {
      rawWebSocket.on("message", (frame, isBinary) => {
        if (isBinary && frame.length === this.frameByteLength)
          handleFrame(frame);
      });
    });
  }

  close() {
    this.webSocketServer.close();
  }
}

module.exports = { WebSocketFrameSocketServer };
