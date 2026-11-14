const { DelayedVoiceLevels } = require("./delayed-voice-levels");

class ConnectedClientRegistry {
  constructor(schedule = setTimeout, now = Date.now) {
    this.agentConnections = new Set();
    this.rendererConnection = null;
    this.viewerConnections = new Set();
    this.stageConnection = null;
    this.seatConnection = null;
    this.voiceLevelsByDisplayCopy = {
      viewer: new DelayedVoiceLevels(
        (payload) => this.sendToViewers(payload),
        schedule,
        now,
      ),
      stage: new DelayedVoiceLevels(
        (payload) => this.stageConnection?.sendJson(payload),
        schedule,
        now,
      ),
    };
  }

  registerSeat(connection) {
    this.seatConnection = connection;
    console.log("✅ Seat connected (voice delay)");
  }

  isSeat(connection) {
    return this.seatConnection === connection;
  }

  followVoiceDelay(delaysByDisplayCopy) {
    for (const [role, voiceLevels] of Object.entries(
      this.voiceLevelsByDisplayCopy,
    ))
      voiceLevels.followVoiceDelay(delaysByDisplayCopy[role]);
  }

  forgetSeat() {
    this.seatConnection = null;
    for (const voiceLevels of Object.values(this.voiceLevelsByDisplayCopy))
      voiceLevels.forgetVoiceDelay();
    console.log("❌ Seat disconnected");
  }

  sendToViewers(payload) {
    this.viewerConnections.forEach((connection) => {
      connection.sendJson(payload);
    });
  }

  sendVoiceLevel(level) {
    const payload = { type: "audioLevel", level };
    for (const voiceLevels of Object.values(this.voiceLevelsByDisplayCopy))
      voiceLevels.send(payload);
    return this.rendererConnection?.sendJson(payload) ?? false;
  }

  registerAgent(connection) {
    this.agentConnections.add(connection);
    console.log("✅ Agent connected (controller)");
  }

  registerRenderer(connection) {
    if (this.rendererConnection && this.rendererConnection !== connection) {
      console.warn(
        "⚠️ Renderer already connected, replacing reference (old connection left to expire)",
      );
    }
    this.rendererConnection = connection;
    console.log("✅ Renderer connected (display)");
  }

  registerViewer(connection) {
    this.viewerConnections.add(connection);
    console.log("✅ Viewer connected (display copy)");
  }

  registerStage(connection) {
    this.stageConnection = connection;
    console.log("✅ Stage connected (call picture)");
  }

  forget(connection) {
    if (this.isSeat(connection)) {
      this.forgetSeat();
      return;
    }
    if (this.forgetDisplayCopy(connection)) {
      return;
    }
    if (this.isAgent(connection)) {
      this.agentConnections.delete(connection);
      console.log("❌ Agent disconnected");
      return;
    }
    if (this.isRenderer(connection)) {
      this.rendererConnection = null;
      console.log("❌ Renderer disconnected");
    }
  }

  forgetDisplayCopy(connection) {
    if (this.isStage(connection)) {
      this.stageConnection = null;
      console.log("❌ Stage disconnected");
      return true;
    }
    if (!this.viewerConnections.delete(connection)) {
      return false;
    }
    console.log("❌ Viewer disconnected");
    return true;
  }

  isAgent(connection) {
    return this.agentConnections.has(connection);
  }

  isRenderer(connection) {
    return this.rendererConnection === connection;
  }

  isViewer(connection) {
    return this.viewerConnections.has(connection);
  }

  isStage(connection) {
    return this.stageConnection === connection;
  }

  displayCopies() {
    return [...this.viewerConnections, this.stageConnection].filter(Boolean);
  }

  hasRenderer() {
    return this.rendererConnection !== null;
  }

  sendToRenderer(payload) {
    this.displayCopies().forEach((connection) => {
      connection.sendJson(payload);
    });
    if (!this.rendererConnection) {
      return false;
    }
    return this.rendererConnection.sendJson(payload);
  }

  sendToCameraOwner(payload) {
    const owner = this.stageConnection ?? this.rendererConnection;
    if (!owner) {
      return false;
    }
    return owner.sendJson(payload);
  }

  sendToAgents(payload) {
    this.agentConnections.forEach((connection) => {
      connection.sendJson(payload);
    });
  }

  closeAll() {
    this.agentConnections.forEach((connection) => {
      connection.close();
    });
    this.displayCopies().forEach((connection) => {
      connection.close();
    });
    this.seatConnection?.close();
    this.rendererConnection?.close();
  }

  connectionSummary() {
    return {
      agentConnected: this.agentConnections.size > 0,
      rendererConnected: this.rendererConnection !== null,
    };
  }
}

module.exports = { ConnectedClientRegistry };
