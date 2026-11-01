#!/usr/bin/env node
const { readCanvasFrame } = require("./virtual-camera/canvas-frame-reader");
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
const AVATAR_RENDERER_URL = `http://localhost:${AVATAR_RENDERER_PORT}/?output=1`;

const numericArgument = (flagName, fallback) =>
  parseInt(
    process.argv.find((_, index, all) => all[index - 1] === flagName) ||
      fallback,
    10,
  );

const CONFIG = {
  CDP_PORT: parseInt(process.env.CDP_PORT || "9222", 10),
  V4L2_DEVICE: process.env.V4L2_DEVICE || "/dev/video10",
  FPS: numericArgument("--fps", "15"),
  WIDTH: numericArgument("--width", "1280"),
  HEIGHT: numericArgument("--height", "720"),
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
    `localhost:${AVATAR_RENDERER_PORT}/?output=1`,
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

async function captureFrames(session, framePipeline) {
  let frameCount = 0;
  let closed = false;
  session.onClosed(() => {
    closed = true;
  });
  while (!closed) {
    const started = performance.now();
    const frame = await readCanvasFrame(session, CONFIG.SCREENCAST_QUALITY);
    if (closed) return;
    if (frame && framePipeline.writeFrame(frame)) frameCount++;
    reportFrameCount(frameCount);
    await new Promise((resolve) =>
      setTimeout(
        resolve,
        Math.max(1, 1000 / CONFIG.FPS - (performance.now() - started)),
      ),
    );
  }
}

function reportFrameCount(frameCount) {
  if (frameCount && frameCount % (CONFIG.FPS * 5) === 0)
    console.log(`Frames captured: ${frameCount}`);
}

function registerShutdownHandlers(session, framePipeline) {
  process.on("SIGINT", () => {
    console.log("\n🛑 Stopping virtual camera...");
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
    await session.sendAndAwaitResult("Emulation.setDeviceMetricsOverride", {
      width: CONFIG.WIDTH,
      height: CONFIG.HEIGHT,
      deviceScaleFactor: 1,
      mobile: false,
    });
    await dismissStartModal(session);

    captureFrames(session, framePipeline).catch((error) => {
      console.error(error.message);
      process.exitCode = 1;
      framePipeline.end();
      session.close();
    });
  });

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
