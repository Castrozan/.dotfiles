const express = require("express");
const http = require("http");
const { AudioFileHttpServerPort } = require("./audio-file-http-server-port");

class ExpressAudioFileHttpServer extends AudioFileHttpServerPort {
  constructor() {
    super();
    this.expressApplication = express();
    this.nodeHttpServer = null;
  }

  allowCrossOriginReadsFrom(allowedOrigins) {
    this.expressApplication.use((request, response, next) => {
      const requestOrigin = request.headers.origin;
      if (requestOrigin && allowedOrigins.includes(requestOrigin)) {
        response.setHeader("Access-Control-Allow-Origin", requestOrigin);
      }
      response.setHeader("Vary", "Origin");
      response.setHeader("Access-Control-Allow-Methods", "GET");
      response.setHeader("Access-Control-Allow-Headers", "Content-Type");
      next();
    });
  }

  serveDirectoryAtRoute(routePath, directoryPath) {
    this.expressApplication.use(
      routePath,
      express.static(directoryPath, { dotfiles: "deny", index: false }),
    );
  }

  serveJsonAtRoute(routePath, buildJsonPayload) {
    this.expressApplication.get(routePath, (request, response) => {
      response.json(buildJsonPayload());
    });
  }

  listen(portNumber, onListening) {
    this.nodeHttpServer = http.createServer(this.expressApplication);
    this.nodeHttpServer.listen(portNumber, onListening);
  }

  close() {
    this.nodeHttpServer?.close();
  }
}

module.exports = { ExpressAudioFileHttpServer };
