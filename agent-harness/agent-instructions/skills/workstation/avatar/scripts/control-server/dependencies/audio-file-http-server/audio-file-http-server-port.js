const notImplemented = (methodName) => {
  throw new Error(
    `AudioFileHttpServerPort.${methodName} must be implemented by an adapter`,
  );
};

class AudioFileHttpServerPort {
  allowCrossOriginReadsFrom(allowedOrigins) {
    notImplemented("allowCrossOriginReadsFrom");
  }

  serveDirectoryAtRoute(routePath, directoryPath) {
    notImplemented("serveDirectoryAtRoute");
  }

  serveJsonAtRoute(routePath, buildJsonPayload) {
    notImplemented("serveJsonAtRoute");
  }

  listen(portNumber, onListening) {
    notImplemented("listen");
  }

  close() {
    notImplemented("close");
  }
}

module.exports = { AudioFileHttpServerPort };
