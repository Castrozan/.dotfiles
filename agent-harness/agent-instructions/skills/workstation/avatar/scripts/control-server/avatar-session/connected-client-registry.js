class ConnectedClientRegistry {
  constructor() {
    this.agentConnections = new Set();
    this.rendererConnection = null;
    this.viewerConnections = new Set();
    this.stageConnection = null;
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
    if (this.isStage(connection)) {
      this.stageConnection = null;
      console.log("❌ Stage disconnected");
      return;
    }
    if (this.viewerConnections.delete(connection)) {
      console.log("❌ Viewer disconnected");
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
