class ConnectedClientRegistry {
  constructor() {
    this.agentConnections = new Set();
    this.rendererConnection = null;
    this.viewerConnections = new Set();
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

  forget(connection) {
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

  hasRenderer() {
    return this.rendererConnection !== null;
  }

  sendToRenderer(payload) {
    this.viewerConnections.forEach((connection) => {
      connection.sendJson(payload);
    });
    if (!this.rendererConnection) {
      return false;
    }
    return this.rendererConnection.sendJson(payload);
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
    this.viewerConnections.forEach((connection) => {
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
