const AVATAR_STATES = {
  IDLE: "idle",
  SPEAKING: "speaking",
  TRANSITIONING: "transitioning",
};

class AvatarStateStore {
  constructor() {
    this.current = AVATAR_STATES.IDLE;
    this.currentExpression = "neutral";
    this.currentIdleMode = "breathing";
    this.intensity = 1.0;
    this.speaking = false;
    this.startedAt = Date.now();
  }

  beginSpeaking(expression) {
    this.current = AVATAR_STATES.SPEAKING;
    this.speaking = true;
    this.currentExpression = expression;
  }

  finishSpeaking() {
    this.current = AVATAR_STATES.IDLE;
    this.speaking = false;
  }

  finishSpeakingIfStillSpeaking() {
    if (this.current !== AVATAR_STATES.SPEAKING) {
      return false;
    }
    this.finishSpeaking();
    return true;
  }

  applyExpression(expressionName, intensity) {
    this.currentExpression = expressionName;
    this.intensity = intensity;
  }

  applyIdleMode(idleMode) {
    this.currentIdleMode = idleMode;
  }

  uptimeSeconds() {
    return Math.floor((Date.now() - this.startedAt) / 1000);
  }
}

module.exports = { AvatarStateStore, AVATAR_STATES };
