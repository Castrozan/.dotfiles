const MOUTH_OPENING_AT_PEAK = 0.8;
const MINIMUM_VOICE_PEAK = 0.08;
const VOICE_PEAK_DECAY = 0.995;
const MOUTH_OPENING_RATE = 30;
const MOUTH_CLOSING_RATE = 12;
const VOICE_LEVEL_THRESHOLD = 0.02;
const VOICE_HOLD_MILLISECONDS = 400;

export function followLevel(current, target, deltaSeconds) {
  const rate = target > current ? MOUTH_OPENING_RATE : MOUTH_CLOSING_RATE;
  return current + (target - current) * (1 - Math.exp(-rate * deltaSeconds));
}

export function followVoicePeak(peak, level) {
  return Math.max(level, peak * VOICE_PEAK_DECAY, MINIMUM_VOICE_PEAK);
}

export function mouthOpening(level, voicePeak) {
  return Math.max(0, (level / voicePeak) * MOUTH_OPENING_AT_PEAK);
}

export function emotionMouthTarget(timestamp, lastVoiceTime) {
  return timestamp - lastVoiceTime < VOICE_HOLD_MILLISECONDS ? 0 : 1;
}

export function visibleMode(mode, speaking) {
  return mode === "camera" && speaking ? "avatar" : mode;
}

export function statusIsHidden(pageOptions) {
  return pageOptions.has("output") || pageOptions.has("bare");
}

export class RendererControls {
  constructor(state, actions, role = "renderer") {
    this.state = state;
    this.actions = actions;
    this.role = role;
    this.voicePeak = 0;
    this.handlers = {
      audioLevel: ({ level }) => {
        this.voicePeak = followVoicePeak(this.voicePeak, level);
        state.mouthTarget = mouthOpening(level, this.voicePeak);
        state.lastLevelTime = performance.now();
        if (level > VOICE_LEVEL_THRESHOLD)
          state.lastVoiceTime = state.lastLevelTime;
        window.avatarStatus.levelMessages++;
      },
      updateExpression: actions.setExpression,
      setIdle: (message) => {
        state.idleMode = message.mode;
      },
      setPresented: ({ presented }) => actions.setPresented(presented),
      startSpeaking: (message) => {
        state.speaking = true;
        actions.beginSpeech(message);
      },
      speechEnded: () => {
        state.speaking = false;
        actions.endSpeech();
      },
      perform: this.requestPerformance.bind(this),
      setVideoMode: this.requestVideoMode.bind(this),
      setCharacter: this.requestCharacter.bind(this),
      listCameras: this.reportCameras.bind(this),
      enableCamera: (message) =>
        this.chooseCamera(message, () =>
          actions.enableCamera(message.deviceId),
        ),
      disableCamera: (message) =>
        this.chooseCamera(message, actions.disableCamera),
    };
  }

  connect() {
    this.socket = new WebSocket("ws://127.0.0.1:8765");
    this.socket.onopen = () => {
      this.socket.send(JSON.stringify({ type: "identify", role: this.role }));
      if (this.role !== "renderer") return;
      this.socket.send(
        JSON.stringify({
          type: "characterChanged",
          name: this.actions.currentCharacter(),
        }),
      );
    };
    this.socket.onmessage = (event) => this.dispatch(JSON.parse(event.data));
    this.socket.onclose = () => {
      this.state.mouthTarget = 0;
      this.state.speaking = false;
      setTimeout(() => this.connect(), 1500);
    };
  }

  dispatch(message) {
    if (Object.hasOwn(this.handlers, message.type))
      return this.handlers[message.type](message);
    return undefined;
  }

  requestPerformance({ action, name, id }) {
    try {
      const result = this.actions.perform(action, name);
      this.socket.send(
        JSON.stringify({
          type: "performanceApplied",
          action,
          name,
          result,
          id,
        }),
      );
    } catch (error) {
      this.socket.send(
        JSON.stringify({
          type: "performanceError",
          message: error.message,
          id,
        }),
      );
    }
  }

  async requestVideoMode(message) {
    try {
      await this.actions.showMode(message.mode);
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

  async requestCharacter(message) {
    try {
      await this.actions.showCharacter(message.name);
      this.socket.send(
        JSON.stringify({
          type: "characterChanged",
          name: message.name,
          id: message.id,
        }),
      );
    } catch (error) {
      this.socket.send(
        JSON.stringify({
          type: "characterError",
          message: error.message,
          id: message.id,
        }),
      );
    }
  }

  async reportCameras({ id }) {
    this.socket.send(
      JSON.stringify({
        type: "cameraList",
        cameras: await this.actions.cameras(),
        id,
      }),
    );
  }

  async chooseCamera({ id }, choose) {
    let message;
    try {
      await choose();
      message = this.actions.cameraActive()
        ? "Camera enabled"
        : "Camera released";
    } catch (error) {
      message = error.message;
    }
    this.socket.send(JSON.stringify({ type: "cameraResult", message, id }));
  }
}
