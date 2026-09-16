#!/usr/bin/env node
const {
  ExpressAudioFileHttpServer,
} = require("./dependencies/audio-file-http-server/express-audio-file-http-server");
const {
  WebSocketMessageSocketServer,
} = require("./dependencies/message-socket-server/websocket-message-socket-server");
const { AvatarStateStore } = require("./avatar-session/avatar-state-store");
const {
  ConnectedClientRegistry,
} = require("./avatar-session/connected-client-registry");
const {
  attachClientConnection,
} = require("./avatar-session/client-connection-router");
const { TextToSpeechGenerator } = require("./speech/text-to-speech-generator");

const RENDERER_PORT = process.env.AVATAR_RENDERER_PORT || "3000";

const CONFIG = {
  WS_PORT: parseInt(process.env.AVATAR_WS_PORT || "8765"),
  HTTP_PORT: parseInt(process.env.AVATAR_HTTP_PORT || "8766"),
  TTS_VOICE: process.env.AVATAR_TTS_VOICE || "@ttsVoice@",
  TTS_DIR: "/tmp/clever-avatar-tts",
  SPEAKER_SINK: "default",
  KEEP_ALIVE_INTERVAL_MS: 30000,
  RENDERER_ORIGINS: [
    `http://localhost:${RENDERER_PORT}`,
    `http://127.0.0.1:${RENDERER_PORT}`,
  ],
};

function startAudioFileHttpServer(avatarState, clientRegistry) {
  const httpServer = new ExpressAudioFileHttpServer();

  httpServer.allowCrossOriginReadsFrom(CONFIG.RENDERER_ORIGINS);
  httpServer.serveDirectoryAtRoute("/audio", CONFIG.TTS_DIR);
  httpServer.serveJsonAtRoute("/health", () => ({
    status: "ok",
    uptime: avatarState.uptimeSeconds(),
    state: avatarState.current,
    ...clientRegistry.connectionSummary(),
  }));

  httpServer.listen(CONFIG.HTTP_PORT, () => {
    console.log(`🌐 HTTP server listening on port ${CONFIG.HTTP_PORT}`);
    console.log(`   Audio URL: http://localhost:${CONFIG.HTTP_PORT}/audio/`);
    console.log(`   Health check: http://localhost:${CONFIG.HTTP_PORT}/health`);
  });

  return httpServer;
}

function startAvatarSocketServer(context) {
  const socketServer = new WebSocketMessageSocketServer(CONFIG.WS_PORT);

  socketServer.onConnection((connection) =>
    attachClientConnection(connection, context),
  );
  socketServer.startKeepAlive(CONFIG.KEEP_ALIVE_INTERVAL_MS);

  console.log(`🔌 WebSocket server listening on port ${CONFIG.WS_PORT}`);
  console.log(`   Agent URL: ws://localhost:${CONFIG.WS_PORT}`);
  console.log(`   Renderer URL: ws://localhost:${CONFIG.WS_PORT}`);

  return socketServer;
}

function printUsageInstructions() {
  console.log("");
  console.log("✅ Avatar Control Server ready!");
  console.log("");
  console.log("📋 Connection Instructions:");
  console.log('   Agent: Send { type: "identify", role: "agent" }');
  console.log('   Renderer: Send { type: "identify", role: "renderer" }');
  console.log("");
  console.log("📋 Agent Commands:");
  console.log(
    '   { type: "speak", text: "Hello", emotion: "happy", output: "mic" }',
  );
  console.log('   output: "speakers" (room) | "mic" (Meet) | "both"');
  console.log(
    '   { type: "setExpression", name: "surprised", intensity: 0.8 }',
  );
  console.log('   { type: "setIdle", mode: "breathing" }');
  console.log('   { type: "getStatus" }');
  console.log("");
}

async function main() {
  console.log("🚀 Starting Clever Avatar Control Server...");
  console.log("");

  const avatarState = new AvatarStateStore();
  const clientRegistry = new ConnectedClientRegistry();
  const textToSpeechGenerator = new TextToSpeechGenerator(
    CONFIG.TTS_DIR,
    CONFIG.TTS_VOICE,
  );
  await textToSpeechGenerator.prepareOutputRootDirectory();

  const context = {
    avatarState,
    clientRegistry,
    textToSpeechGenerator,
    speakerSinkName: CONFIG.SPEAKER_SINK,
  };

  const httpServer = startAudioFileHttpServer(avatarState, clientRegistry);
  const socketServer = startAvatarSocketServer(context);

  printUsageInstructions();

  process.on("SIGINT", () => {
    console.log("\n🛑 Shutting down...");
    clientRegistry.closeAll();
    socketServer.close();
    httpServer.close();
    process.exit(0);
  });
}

main().catch((error) => {
  console.error("💥 Fatal error:", error);
  process.exit(1);
});
