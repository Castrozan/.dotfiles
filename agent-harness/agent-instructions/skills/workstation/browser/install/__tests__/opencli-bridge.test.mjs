import assert from "node:assert/strict";
import { once } from "node:events";
import { createRequire } from "node:module";
import { randomBytes } from "node:crypto";
import { spawn } from "node:child_process";
import { after, before, test } from "node:test";
import { setTimeout } from "node:timers/promises";
import { pathToFileURL } from "node:url";

const packageRoot = process.env.OPENCLI_PACKAGE_ROOT;
const require = createRequire(`${packageRoot}/package.json`);
const { WebSocket } = require("ws");
const token = randomBytes(32).toString("hex");
let daemon;

before(async () => {
  daemon = spawn(process.execPath, [`${packageRoot}/dist/src/daemon.js`], {
    env: { ...process.env, OPENCLI_BRIDGE_TOKEN: token },
    stdio: "ignore",
  });
  for (let attempt = 0; attempt < 50; attempt++) {
    assert.equal(daemon.exitCode, null, "The test must own its daemon");
    try {
      const response = await fetch("http://127.0.0.1:19825/ping");
      if (response.ok) return;
    } catch {}
    await setTimeout(50);
  }
  throw new Error("The owned test daemon failed to start");
});

after(async () => {
  if (daemon?.exitCode === null) {
    daemon.kill("SIGTERM");
    await once(daemon, "exit");
  }
});

function connectionResult(query, origin) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(`ws://127.0.0.1:19825/ext${query}`, {
      ...(origin && { origin }),
      handshakeTimeout: 2000,
    });
    socket.once("open", () => {
      socket.once("close", () => resolve(101));
      socket.close();
    });
    socket.once("unexpected-response", (_request, response) => {
      response.resume();
      socket.terminate();
      resolve(response.statusCode);
    });
    socket.once("error", reject);
  });
}

test("only the token-bearing extension can join the job Bridge", async () => {
  const origin = "chrome-extension://owned-test-extension";
  assert.equal(await connectionResult("", origin), 401);
  assert.equal(await connectionResult("?token=wrong", origin), 401);
  assert.equal(await connectionResult(`?token=${token}`), 401);
  assert.equal(
    await connectionResult(`?token=${token}`, "https://example.com"),
    401,
  );
  assert.equal(await connectionResult(`?token=${token}`, origin), 101);
});

test("CLI failure cannot silently create a detached daemon", async () => {
  const lifecycle = await import(
    pathToFileURL(`${packageRoot}/dist/src/browser/daemon-lifecycle.js`)
  );
  assert.throws(() => lifecycle.spawnDaemonProcess(), /opencli-run/);
});

test("browser commands require the job bearer token", async () => {
  const request = {
    method: "POST",
    headers: { "X-OpenCLI": "1", "Content-Type": "application/json" },
    body: JSON.stringify({
      id: "authentication-proof",
      action: "tabs",
      op: "list",
      session: "proof",
    }),
  };
  const denied = await fetch("http://127.0.0.1:19825/command", request);
  assert.equal(denied.status, 403);
  const accepted = await fetch("http://127.0.0.1:19825/command", {
    ...request,
    headers: { ...request.headers, Authorization: `Bearer ${token}` },
  });
  assert.equal(accepted.status, 503);
});
