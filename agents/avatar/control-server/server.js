#!/usr/bin/env node
/**
 * Clever's Avatar Control Server
 *
 * WebSocket coordinator between OpenClaw agent and avatar renderer.
 * Manages avatar state, TTS generation, and command forwarding.
 */

const WebSocket = require("ws");
const express = require("express");
const http = require("http");
const { exec } = require("child_process");
const { promisify } = require("util");
const fs = require("fs").promises;
const path = require("path");

const execAsync = promisify(exec);

// Configuration
const CONFIG = {
  WS_PORT: 8765,
  HTTP_PORT: 8766,
  TTS_VOICE: "@ttsVoice@",
  TTS_DIR: "/tmp/clever-avatar-tts",
  AUDIO_DEVICE: "Clever_TTS_Output",
};

// State machine
const STATES = {
  IDLE: "idle",
  SPEAKING: "speaking",
  TRANSITIONING: "transitioning",
};

// Global state
const state = {
  current: STATES.IDLE,
  currentExpression: "neutral",
  currentIdleMode: "breathing",
  intensity: 1.0,
  speaking: false,
  uptime: Date.now(),
  agentConnected: false,
  rendererConnected: false,
};

// Connected clients
const clients = {
  agent: null, // Controller (OpenClaw agent)
  renderer: null, // Display (browser avatar)
};

// Create TTS directory
async function initTTSDirectory() {
  try {
    await fs.mkdir(CONFIG.TTS_DIR, { recursive: true });
    console.log(`✅ TTS directory: ${CONFIG.TTS_DIR}`);
  } catch (err) {
    console.error("❌ Failed to create TTS directory:", err.message);
  }
}

// Generate TTS audio with edge-tts
async function generateTTS(text, outputId) {
  const outputDir = path.join(CONFIG.TTS_DIR, outputId);
  const audioPath = path.join(outputDir, "voice.mp3");
  const timingPath = path.join(outputDir, "timing.json");

  try {
    // Create output directory
    await fs.mkdir(outputDir, { recursive: true });

    // Generate TTS with timing data
    const command =
      `edge-tts --text "${text.replace(/"/g, '\\"')}" ` +
      `--voice ${CONFIG.TTS_VOICE} ` +
      `--rate +0% ` +
      `--write-media ${audioPath} ` +
      `--write-subtitles ${timingPath}`;

    console.log(
      `🎤 Generating TTS: "${text.substring(0, 50)}${text.length > 50 ? "..." : ""}"`,
    );
    await execAsync(command);

    // Read timing data
    const timingData = await fs.readFile(timingPath, "utf-8");
    const timing = parseTimingData(timingData);

    return {
      audioPath,
      audioUrl: `/audio/${outputId}/voice.mp3`,
      timing,
      duration: timing.length > 0 ? timing[timing.length - 1].end : 0,
    };
  } catch (err) {
    console.error("❌ TTS generation failed:", err.message);
    throw err;
  }
}

// Parse timing data from edge-tts subtitles (VTT/SRT format)
function parseTimingData(srtData) {
  try {
    const timing = [];
    // Match SRT blocks: index, timestamp line, text line
    const blocks = srtData.trim().split(/\n\n+/);

    for (const block of blocks) {
      const lines = block.trim().split("\n");
      if (lines.length < 2) continue;

      // Find the timestamp line (contains -->)
      const tsLine = lines.find((l) => l.includes("-->"));
      if (!tsLine) continue;

      const match = tsLine.match(
        /(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})/,
      );
      if (!match) continue;

      const start =
        parseInt(match[1]) * 3600 +
        parseInt(match[2]) * 60 +
        parseInt(match[3]) +
        parseInt(match[4]) / 1000;
      const end =
        parseInt(match[5]) * 3600 +
        parseInt(match[6]) * 60 +
        parseInt(match[7]) +
        parseInt(match[8]) / 1000;

      // Text is everything after the timestamp line
      const tsIdx = lines.indexOf(tsLine);
      const text = lines
        .slice(tsIdx + 1)
        .join(" ")
        .trim();
      if (!text) continue;

      // Split text into words for per-word timing
      const words = text.split(/\s+/);
      const wordDuration = (end - start) / words.length;

      for (let i = 0; i < words.length; i++) {
        timing.push({
          start: start + i * wordDuration,
          end: start + (i + 1) * wordDuration,
          text: words[i],
          phoneme: approximatePhoneme(words[i]),
        });
      }
    }

    return timing;
  } catch (err) {
    console.warn("⚠️ Failed to parse timing data:", err.message);
    return [];
  }
}

// Approximate phoneme from word (simple heuristic)
function approximatePhoneme(word) {
  if (!word) return "neutral";

  const vowels = {
    a: ["a", "ah", "ay"],
    e: ["e", "eh", "ee"],
    i: ["i", "ih", "ee"],
    o: ["o", "oh", "aw"],
    u: ["u", "uh", "oo"],
  };

  const firstVowel = word.toLowerCase().match(/[aeiou]/)?.[0];
  return firstVowel || "neutral";
}

// Handle agent commands
async function handleAgentCommand(message, ws) {
  try {
    const command = JSON.parse(message);
    console.log(`📥 Agent command: ${command.type}`);

    switch (command.type) {
      case "speak":
        await handleSpeak(command, ws);
        break;

      case "setExpression":
        await handleSetExpression(command, ws);
        break;

      case "setIdle":
        await handleSetIdle(command, ws);
        break;

      case "getStatus":
        await handleGetStatus(command, ws);
        break;

      default:
        sendError(ws, `Unknown command type: ${command.type}`);
    }
  } catch (err) {
    console.error("❌ Error handling command:", err.message);
    sendError(ws, err.message);
  }
}

// Handle speak command
async function handleSpeak(command, ws) {
  const { text, emotion = "neutral", id = Date.now().toString() } = command;

  if (!text) {
    sendError(ws, "Missing required field: text");
    return;
  }

  // Update state
  state.current = STATES.SPEAKING;
  state.speaking = true;
  state.currentExpression = emotion;

  try {
    // Generate TTS
    const tts = await generateTTS(text, id);

    // Send to renderer
    if (clients.renderer) {
      const rendererCommand = {
        type: "startSpeaking",
        id,
        audioUrl: tts.audioUrl,
        timing: tts.timing,
        emotion,
        text,
      };

      clients.renderer.send(JSON.stringify(rendererCommand));
      console.log(
        `📤 Forwarded to renderer: startSpeaking (${tts.timing.length} phonemes)`,
      );
    }

    // Send acknowledgment to agent
    sendResponse(ws, {
      type: "speakAck",
      id,
      duration: tts.duration,
      status: "started",
    });

    // Auto-transition back to idle after duration
    setTimeout(
      () => {
        if (state.current === STATES.SPEAKING) {
          state.current = STATES.IDLE;
          state.speaking = false;
          console.log("🔄 Auto-transitioned to IDLE");
        }
      },
      (tts.duration + 0.5) * 1000,
    ); // Add 500ms buffer
  } catch (err) {
    state.current = STATES.IDLE;
    state.speaking = false;
    sendError(ws, `TTS generation failed: ${err.message}`);
  }
}

// Handle setExpression command
async function handleSetExpression(command, ws) {
  const { name, intensity = 1.0, duration = 2000 } = command;

  if (!name) {
    sendError(ws, "Missing required field: name");
    return;
  }

  // Update state
  state.currentExpression = name;
  state.intensity = intensity;

  // Forward to renderer
  if (clients.renderer) {
    const rendererCommand = {
      type: "updateExpression",
      expression: name,
      intensity,
      transitionMs: duration,
    };

    clients.renderer.send(JSON.stringify(rendererCommand));
    console.log(
      `📤 Forwarded to renderer: updateExpression (${name}, ${intensity})`,
    );
  }

  // Send acknowledgment
  sendResponse(ws, {
    type: "expressionAck",
    expression: name,
    intensity,
    status: "updated",
  });
}

// Handle setIdle command
async function handleSetIdle(command, ws) {
  const { mode = "breathing" } = command;

  // Update state
  state.currentIdleMode = mode;

  // Forward to renderer
  if (clients.renderer) {
    const rendererCommand = {
      type: "setIdle",
      mode,
    };

    clients.renderer.send(JSON.stringify(rendererCommand));
    console.log(`📤 Forwarded to renderer: setIdle (${mode})`);
  }

  // Send acknowledgment
  sendResponse(ws, {
    type: "idleAck",
    mode,
    status: "updated",
  });
}

// Handle getStatus command
async function handleGetStatus(command, ws) {
  const status = {
    type: "status",
    state: state.current,
    currentExpression: state.currentExpression,
    currentIdleMode: state.currentIdleMode,
    intensity: state.intensity,
    speaking: state.speaking,
    uptime: Math.floor((Date.now() - state.uptime) / 1000),
    agentConnected: state.agentConnected,
    rendererConnected: state.rendererConnected,
    timestamp: Date.now(),
  };

  sendResponse(ws, status);
  console.log("📤 Sent status to agent");
}

// Send response to client
function sendResponse(ws, data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

// Send error to client
function sendError(ws, message) {
  sendResponse(ws, {
    type: "error",
    error: message,
    timestamp: Date.now(),
  });
}

// Setup HTTP server for audio files
function setupHTTPServer() {
  const app = express();

  // Enable CORS
  app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Methods", "GET");
    res.header("Access-Control-Allow-Headers", "Content-Type");
    next();
  });

  // Serve audio files
  app.use("/audio", express.static(CONFIG.TTS_DIR));

  // Health check
  app.get("/health", (req, res) => {
    res.json({
      status: "ok",
      uptime: Math.floor((Date.now() - state.uptime) / 1000),
      state: state.current,
      agentConnected: state.agentConnected,
      rendererConnected: state.rendererConnected,
    });
  });

  const server = http.createServer(app);
  server.listen(CONFIG.HTTP_PORT, () => {
    console.log(`🌐 HTTP server listening on port ${CONFIG.HTTP_PORT}`);
    console.log(`   Audio URL: http://localhost:${CONFIG.HTTP_PORT}/audio/`);
    console.log(`   Health check: http://localhost:${CONFIG.HTTP_PORT}/health`);
  });

  return server;
}

// Setup WebSocket server
function setupWebSocketServer() {
  const wss = new WebSocket.Server({ port: CONFIG.WS_PORT });

  // Ping/pong keepalive — prevents idle disconnects
  const pingInterval = setInterval(() => {
    wss.clients.forEach((ws) => {
      if (ws.isAlive === false) {
        console.log("💀 Terminating unresponsive client");
        return ws.terminate();
      }
      ws.isAlive = false;
      ws.ping();
    });
  }, 30000); // Every 30s

  wss.on("close", () => clearInterval(pingInterval));

  wss.on("connection", (ws, req) => {
    console.log("🔌 New WebSocket connection");
    ws.isAlive = true;
    ws.on("pong", () => {
      ws.isAlive = true;
    });

    // Determine client role from query params or first message
    ws.on("message", async (message) => {
      try {
        const data = JSON.parse(message);

        // Handle client identification
        if (data.type === "identify") {
          const role = data.role; // 'agent' or 'renderer'

          if (role === "agent") {
            if (clients.agent) {
              console.warn("⚠️ Agent already connected, replacing...");
              clients.agent.close();
            }
            clients.agent = ws;
            state.agentConnected = true;
            console.log("✅ Agent connected (controller)");

            sendResponse(ws, {
              type: "identifyAck",
              role: "agent",
              status: "connected",
              serverVersion: "1.0.0",
            });
          } else if (role === "renderer") {
            if (clients.renderer && clients.renderer !== ws) {
              console.warn(
                "⚠️ Renderer already connected, replacing reference (old connection left to expire)",
              );
              // DON'T close the old one — closing triggers onclose → reconnect → identify → close loop
              // Just null its handlers so it doesn't interfere, and let it die naturally
              clients.renderer.onclose = null;
              clients.renderer.onerror = null;
            }
            clients.renderer = ws;
            state.rendererConnected = true;
            console.log("✅ Renderer connected (display)");

            sendResponse(ws, {
              type: "identifyAck",
              role: "renderer",
              status: "connected",
              serverVersion: "1.0.0",
            });

            // Send current state to new renderer
            sendResponse(ws, {
              type: "initialState",
              state: state.current,
              expression: state.currentExpression,
              idleMode: state.currentIdleMode,
              intensity: state.intensity,
            });
          } else {
            sendError(ws, `Unknown role: ${role}`);
            ws.close();
          }
        } else if (ws === clients.agent) {
          // Handle agent commands
          await handleAgentCommand(message, ws);
        } else if (ws === clients.renderer) {
          // Handle renderer events (e.g., speechEnd notification)
          console.log("📥 Renderer event:", data.type);

          if (data.type === "speechEnd") {
            state.current = STATES.IDLE;
            state.speaking = false;
            console.log("🔄 Speech ended, transitioned to IDLE");
          }
        } else {
          // Unidentified client - send identify request
          sendResponse(ws, {
            type: "identifyRequest",
            message:
              'Please identify with { type: "identify", role: "agent"|"renderer" }',
          });
        }
      } catch (err) {
        console.error("❌ Error processing message:", err.message);
        sendError(ws, `Message processing error: ${err.message}`);
      }
    });

    ws.on("close", () => {
      if (ws === clients.agent) {
        clients.agent = null;
        state.agentConnected = false;
        console.log("❌ Agent disconnected");
      } else if (ws === clients.renderer) {
        clients.renderer = null;
        state.rendererConnected = false;
        console.log("❌ Renderer disconnected");
      }
    });

    ws.on("error", (err) => {
      console.error("❌ WebSocket error:", err.message);
    });
  });

  console.log(`🔌 WebSocket server listening on port ${CONFIG.WS_PORT}`);
  console.log(`   Agent URL: ws://localhost:${CONFIG.WS_PORT}`);
  console.log(`   Renderer URL: ws://localhost:${CONFIG.WS_PORT}`);

  return wss;
}

// Main startup
async function main() {
  console.log("🚀 Starting Clever Avatar Control Server...");
  console.log("");

  // Initialize
  await initTTSDirectory();

  // Start servers
  const httpServer = setupHTTPServer();
  const wsServer = setupWebSocketServer();

  console.log("");
  console.log("✅ Avatar Control Server ready!");
  console.log("");
  console.log("📋 Connection Instructions:");
  console.log('   Agent: Send { type: "identify", role: "agent" }');
  console.log('   Renderer: Send { type: "identify", role: "renderer" }');
  console.log("");
  console.log("📋 Agent Commands:");
  console.log('   { type: "speak", text: "Hello", emotion: "happy" }');
  console.log(
    '   { type: "setExpression", name: "surprised", intensity: 0.8 }',
  );
  console.log('   { type: "setIdle", mode: "breathing" }');
  console.log('   { type: "getStatus" }');
  console.log("");

  // Graceful shutdown
  process.on("SIGINT", () => {
    console.log("\n🛑 Shutting down...");

    if (clients.agent) clients.agent.close();
    if (clients.renderer) clients.renderer.close();

    wsServer.close();
    httpServer.close();

    process.exit(0);
  });
}

// Start server
main().catch((err) => {
  console.error("💥 Fatal error:", err);
  process.exit(1);
});
