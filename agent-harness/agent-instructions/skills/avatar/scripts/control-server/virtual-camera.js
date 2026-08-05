#!/usr/bin/env node
const {
  ChromeDevtoolsTargetLocator,
} = require("./chrome-devtools/chrome-devtools-target-locator");
const {
  ChromeDevtoolsSession,
} = require("./chrome-devtools/chrome-devtools-session");
const {
  WebSocketMessageSocketClient,
} = require("./dependencies/message-socket-client/websocket-message-socket-client");
const {
  ScreencastFramePipeline,
} = require("./virtual-camera/screencast-frame-pipeline");

const AVATAR_RENDERER_PORT = process.env.AVATAR_RENDERER_PORT || "3000";
const AVATAR_RENDERER_URL = `http://localhost:${AVATAR_RENDERER_PORT}`;

const numericArgument = (flagName, fallback) =>
  parseInt(
    process.argv.find((_, index, all) => all[index - 1] === flagName) ||
      fallback,
  );

const CONFIG = {
  CDP_PORT: parseInt(process.env.CDP_PORT || "9222"),
  V4L2_DEVICE: process.env.V4L2_DEVICE || "/dev/video10",
  FPS: numericArgument("--fps", "15"),
  WIDTH: numericArgument("--width", "1280"),
  HEIGHT: numericArgument("--height", "720"),
  FORMAT: "jpeg",
  SCREENCAST_QUALITY: 60,
};

const DISMISS_START_MODAL_EXPRESSION = `(() => {
  const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent.trim() === "Start");
  if (btn) { btn.click(); return "dismissed"; }
  return "no modal";
})()`;

async function resolveRendererDebuggerUrl() {
  const targetLocator = new ChromeDevtoolsTargetLocator(CONFIG.CDP_PORT);
  const rendererTarget = await targetLocator.findOrOpenPageTarget(
    `localhost:${AVATAR_RENDERER_PORT}`,
    AVATAR_RENDERER_URL,
  );

  if (!rendererTarget) {
    throw new Error(
      `ChatVRM tab not found after auto-open. Is the renderer running on port ${AVATAR_RENDERER_PORT}?`,
    );
  }

  console.log(
    `📺 Found ChatVRM tab: ${rendererTarget.title} (${rendererTarget.url})`,
  );
  return rendererTarget.webSocketDebuggerUrl;
}

async function dismissStartModal(session) {
  const evaluationResult = await session.sendAndAwaitResult(
    "Runtime.evaluate",
    {
      expression: DISMISS_START_MODAL_EXPRESSION,
    },
  );
  const modalStatus = evaluationResult?.result?.value || "unknown";
  console.log(`📋 ChatVRM modal: ${modalStatus}`);
  if (modalStatus === "dismissed") {
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}

function streamScreencastFrames(session, framePipeline) {
  let frameCount = 0;

  session.onEvent((message) => {
    if (message.method !== "Page.screencastFrame") {
      return;
    }

    const { sessionId, metadata } = message.params;
    framePipeline.writeFrame(Buffer.from(message.params.data, "base64"));
    session.send("Page.screencastFrameAck", { sessionId });

    frameCount++;
    if (frameCount % (CONFIG.FPS * 5) === 0) {
      console.log(
        `📹 Frames captured: ${frameCount} (${metadata.deviceWidth}x${metadata.deviceHeight})`,
      );
    }
  });
}

function registerShutdownHandlers(session, framePipeline) {
  process.on("SIGINT", () => {
    console.log("\n🛑 Stopping virtual camera...");
    session.send("Page.stopScreencast");
    setTimeout(() => {
      framePipeline.end();
      session.close();
      process.exit(0);
    }, 500);
  });

  process.on("SIGTERM", () => {
    framePipeline.end();
    session.close();
    process.exit(0);
  });
}

async function startCapture() {
  console.log("🎥 Starting Virtual Camera Pipeline");
  console.log(`   Device: ${CONFIG.V4L2_DEVICE}`);
  console.log(`   Resolution: ${CONFIG.WIDTH}x${CONFIG.HEIGHT}`);
  console.log(`   FPS: ${CONFIG.FPS}`);

  const debuggerUrl = await resolveRendererDebuggerUrl();
  console.log(`🔌 Connecting to CDP: ${debuggerUrl}`);

  const framePipeline = new ScreencastFramePipeline({
    framesPerSecond: CONFIG.FPS,
    width: CONFIG.WIDTH,
    height: CONFIG.HEIGHT,
    videoDevice: CONFIG.V4L2_DEVICE,
  });

  const session = new ChromeDevtoolsSession(
    new WebSocketMessageSocketClient(debuggerUrl),
  );

  session.onOpen(async () => {
    console.log("✅ Connected to CDP");
    await dismissStartModal(session);

    session.send("Page.startScreencast", {
      format: CONFIG.FORMAT,
      quality: CONFIG.SCREENCAST_QUALITY,
      maxWidth: CONFIG.WIDTH,
      maxHeight: CONFIG.HEIGHT,
      everyNthFrame: 1,
    });

    console.log("📡 Screencast started. Streaming to virtual camera...");
    console.log("   Press Ctrl+C to stop.");
  });

  streamScreencastFrames(session, framePipeline);

  session.onClosed(() => {
    console.log("❌ CDP connection closed");
    framePipeline.end();
  });

  session.onError((error) => {
    console.error("❌ CDP error:", error.message);
  });

  registerShutdownHandlers(session, framePipeline);
}

startCapture().catch((error) => {
  console.error("❌ Failed to start:", error.message);
  process.exit(1);
});
