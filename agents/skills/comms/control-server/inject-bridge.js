#!/usr/bin/env node
const http = require("http");
const WebSocket = require("ws");
const fs = require("fs");
const path = require("path");

const cdpPort = process.env.CDP_PORT || "9222";
const rendererPort = process.env.AVATAR_RENDERER_PORT || "@avatarRendererPort@";
const bridgePath =
  process.env.BRIDGE_SCRIPT_PATH || path.join(__dirname, "renderer-bridge.js");

function httpGet(url) {
  return new Promise((resolve, reject) => {
    http
      .get(url, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(e);
          }
        });
      })
      .on("error", reject);
  });
}

async function injectBridge() {
  const targets = await httpGet(`http://127.0.0.1:${cdpPort}/json`);
  const rendererTab = targets.find(
    (t) => t.type === "page" && t.url.includes(`localhost:${rendererPort}`),
  );

  if (!rendererTab) {
    console.error("Renderer tab not found on CDP port " + cdpPort);
    process.exit(1);
  }

  const bridgeScript = fs.readFileSync(bridgePath, "utf8");
  const ws = new WebSocket(rendererTab.webSocketDebuggerUrl);

  ws.on("open", () => {
    ws.send(
      JSON.stringify({
        id: 1,
        method: "Runtime.evaluate",
        params: { expression: bridgeScript },
      }),
    );
    setTimeout(() => {
      ws.close();
      process.exit(0);
    }, 1000);
  });

  ws.on("error", (err) => {
    console.error("CDP WebSocket error:", err.message);
    process.exit(1);
  });
}

injectBridge().catch((err) => {
  console.error("Bridge injection failed:", err.message);
  process.exit(1);
});
