import { OpenCode } from "@opencode/client";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { once } from "node:events";
import { isAbsolute } from "node:path";

function signalProcessGroup(processGroupLeaderId, signalName) {
  try {
    process.kill(-processGroupLeaderId, signalName);
  } catch (error) {
    if (error.code !== "ESRCH") throw error;
  }
}

async function closeOpenCodeServer(server, closed) {
  const force = setTimeout(() => {
    if (server.pid) signalProcessGroup(server.pid, "SIGKILL");
  }, 3000);
  if (server.pid) signalProcessGroup(server.pid, "SIGTERM");
  try {
    await closed;
  } finally {
    clearTimeout(force);
  }
}

function awaitServerAddress(server, signal) {
  return new Promise((resolve, reject) => {
    let output = "";
    const timeout = setTimeout(
      () => finish(new Error("OpenCode server startup exceeded 15s")),
      15000,
    );
    const abort = () => finish(signal.reason);
    const failed = (error) => finish(error);
    const exited = (code) =>
      finish(new Error(`OpenCode server exited during startup: ${code}`));
    const receive = (chunk) => {
      output = (output + chunk.toString()).slice(-8192);
      const address = /server listening on (http:\/\/127\.0\.0\.1:\d+)/.exec(
        output,
      );
      if (address) finish(null, address[1]);
    };
    function finish(error, address) {
      clearTimeout(timeout);
      signal.removeEventListener("abort", abort);
      server.removeListener("error", failed);
      server.removeListener("exit", exited);
      server.stdout.removeListener("data", receive);
      server.stderr.removeListener("data", receive);
      server.stdout.resume();
      server.stderr.resume();
      if (error) reject(error);
      else resolve(address);
    }
    signal.addEventListener("abort", abort, { once: true });
    server.once("error", failed);
    server.once("exit", exited);
    server.stdout.on("data", receive);
    server.stderr.on("data", receive);
  });
}

export async function startOpenCodeServer(invocation, configuration, signal) {
  signal.throwIfAborted();
  const executable = process.env.AGENT_EVAL_OPENCODE_BINARY;
  if (!executable || !isAbsolute(executable)) {
    throw new Error(
      "AGENT_EVAL_OPENCODE_BINARY must name an absolute executable",
    );
  }
  const password = randomUUID();
  const server = spawn(
    executable,
    ["serve", "--hostname", "127.0.0.1", "--port", "0"],
    {
      cwd: invocation.working_directory,
      env: {
        ...process.env,
        OPENCODE_PASSWORD: password,
        OPENCODE_CONFIG_CONTENT: JSON.stringify(configuration),
        OPENCODE_DISABLE_AUTOUPDATE: "true",
      },
      detached: true,
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  const closed = once(server, "close").catch(() => {});
  try {
    const baseUrl = await awaitServerAddress(server, signal);
    return {
      client: OpenCode.make({
        baseUrl,
        headers: {
          Authorization: `Basic ${Buffer.from("opencode:" + password).toString("base64")}`,
        },
      }),
      close: () => closeOpenCodeServer(server, closed),
    };
  } catch (error) {
    await closeOpenCodeServer(server, closed);
    throw error;
  }
}
