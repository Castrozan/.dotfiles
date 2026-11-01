const notImplemented = (methodName) => {
  throw new Error(
    `FrameSocketServerPort.${methodName} must be implemented by an adapter`,
  );
};

class FrameSocketServerPort {
  onFrame(_handleFrame) {
    notImplemented("onFrame");
  }

  close() {
    notImplemented("close");
  }
}

module.exports = { FrameSocketServerPort };
