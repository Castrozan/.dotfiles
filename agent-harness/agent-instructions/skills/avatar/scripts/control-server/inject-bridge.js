#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const {
  ChromeDevtoolsTargetLocator,
} = require("./chrome-devtools/chrome-devtools-target-locator");
const {
  ChromeDevtoolsSession,
} = require("./chrome-devtools/chrome-devtools-session");
const {
  WebSocketMessageSocketClient,
} = require("./dependencies/message-socket-client/websocket-message-socket-client");

const devtoolsPort = process.env.CDP_PORT || "9222";
const rendererPort = process.env.AVATAR_RENDERER_PORT || "@avatarRendererPort@";
const bridgePath =
  process.env.BRIDGE_SCRIPT_PATH || path.join(__dirname, "renderer-bridge.js");

async function injectBridge() {
  const targetLocator = new ChromeDevtoolsTargetLocator(devtoolsPort);
  const rendererTarget = await targetLocator.findPageTarget(
    `localhost:${rendererPort}`,
  );

  if (!rendererTarget) {
    console.error("Renderer tab not found on CDP port " + devtoolsPort);
    process.exit(1);
  }

  const bridgeScript = fs.readFileSync(bridgePath, "utf8");
  const session = new ChromeDevtoolsSession(
    new WebSocketMessageSocketClient(rendererTarget.webSocketDebuggerUrl),
  );

  session.onError((error) => {
    console.error("CDP WebSocket error:", error.message);
    process.exit(1);
  });

  session.onOpen(() => {
    session.send("Runtime.evaluate", { expression: bridgeScript });
    setTimeout(() => {
      session.close();
      process.exit(0);
    }, 1000);
  });
}

injectBridge().catch((error) => {
  console.error("Bridge injection failed:", error.message);
  process.exit(1);
});
