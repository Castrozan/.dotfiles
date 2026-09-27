import { OpenCode } from "@opencode/client";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { once } from "node:events";

export async function startOpenCodeServer(invocation, configuration, signal) {
  signal.throwIfAborted();
  const password = randomUUID();
  const server = spawn(
    "opencode",
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
  async function close() {
    const force = setTimeout(() => {
      if (!server.pid) return;
      try {
        process.kill(-server.pid, "SIGKILL");
      } catch (error) {
        if (error.code !== "ESRCH") throw error;
      }
    }, 3000);
    if (server.pid) {
      try {
        process.kill(-server.pid, "SIGTERM");
      } catch (error) {
        if (error.code !== "ESRCH") throw error;
      }
    }
    try {
      await closed;
    } finally {
      clearTimeout(force);
    }
  }
  try {
    const baseUrl = await new Promise((resolve, reject) => {
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
        const address = output.match(
          /server listening on (http:\/\/127\.0\.0\.1:\d+)/,
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
    return {
      client: OpenCode.make({
        baseUrl,
        headers: {
          Authorization: `Basic ${Buffer.from(`opencode:${password}`).toString("base64")}`,
        },
      }),
      close,
    };
  } catch (error) {
    await close();
    throw error;
  }
}
