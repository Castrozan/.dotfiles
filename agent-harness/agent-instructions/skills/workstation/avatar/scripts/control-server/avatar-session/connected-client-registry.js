class ConnectedClientRegistry {
  constructor() {
    this.agentConnection = null;
    this.rendererConnection = null;
  }

  registerAgent(connection) {
    if (this.agentConnection) {
      console.warn("⚠️ Agent already connected, replacing...");
      this.agentConnection.close();
    }
    this.agentConnection = connection;
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

  forget(connection) {
    if (this.isAgent(connection)) {
      this.agentConnection = null;
      console.log("❌ Agent disconnected");
      return;
    }
    if (this.isRenderer(connection)) {
      this.rendererConnection = null;
      console.log("❌ Renderer disconnected");
    }
  }

  isAgent(connection) {
    return this.agentConnection === connection;
  }

  isRenderer(connection) {
    return this.rendererConnection === connection;
  }

  hasRenderer() {
    return this.rendererConnection !== null;
  }

  sendToRenderer(payload) {
    if (!this.rendererConnection) {
      return false;
    }
    return this.rendererConnection.sendJson(payload);
  }

  closeAll() {
    this.agentConnection?.close();
    this.rendererConnection?.close();
  }

  connectionSummary() {
    return {
      agentConnected: this.agentConnection !== null,
      rendererConnected: this.rendererConnection !== null,
    };
  }
}

module.exports = { ConnectedClientRegistry };
