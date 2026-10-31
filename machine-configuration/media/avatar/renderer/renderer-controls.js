export class RendererControls {
  constructor(state, actions) {
    this.state = state;
    this.actions = actions;
    this.channel = new BroadcastChannel("avatar-local-controls");
    this.channel.onmessage = this.handleLocal.bind(this);
    this.handlers = {
      audioLevel: (message) => {
        state.mouth = Math.max(0, Math.min(1, message.level * 5));
        state.lastLevelTime = performance.now();
        window.avatarStatus.levelMessages++;
      },
      updateExpression: actions.setExpression,
      setIdle: (message) => {
        state.idleMode = message.mode;
      },
      startSpeaking: (message) =>
        actions.setExpression({ expression: message.emotion || "neutral" }),
      setVideoMode: this.requestVideoMode.bind(this),
    };
  }

  connect() {
    this.socket = new WebSocket("ws://127.0.0.1:8765");
    this.socket.onopen = () =>
      this.socket.send(JSON.stringify({ type: "identify", role: "renderer" }));
    this.socket.onmessage = (event) => this.dispatch(JSON.parse(event.data));
    this.socket.onclose = () => {
      this.state.mouth = 0;
      setTimeout(() => this.connect(), 1500);
    };
  }

  dispatch(message) {
    if (Object.hasOwn(this.handlers, message.type))
      this.handlers[message.type](message);
  }

  requestVideoMode(message) {
    try {
      this.actions.setMode(message.mode);
      this.socket.send(
        JSON.stringify({
          type: "videoModeChanged",
          mode: this.state.mode,
          id: message.id,
        }),
      );
    } catch (error) {
      this.socket.send(
        JSON.stringify({
          type: "videoModeError",
          message: error.message,
          id: message.id,
        }),
      );
    }
  }

  async handleLocal(event) {
    try {
      if (event.data.type === "enableCamera")
        await this.actions.enableCamera(event.data.deviceId);
      if (event.data.type === "disableCamera") this.actions.disableCamera();
      this.channel.postMessage({
        type: "cameraResult",
        message: this.actions.cameraActive()
          ? "Camera enabled"
          : "Camera released",
      });
    } catch (error) {
      this.channel.postMessage({
        type: "cameraResult",
        message: error.message,
      });
    }
  }
}
