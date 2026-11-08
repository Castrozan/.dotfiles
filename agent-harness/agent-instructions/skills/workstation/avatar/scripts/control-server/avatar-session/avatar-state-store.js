class AvatarStateStore {
  constructor() {
    this.currentExpression = "neutral";
    this.currentIdleMode = "breathing";
    this.intensity = 1.0;
    this.startedAt = Date.now();
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

module.exports = { AvatarStateStore };
