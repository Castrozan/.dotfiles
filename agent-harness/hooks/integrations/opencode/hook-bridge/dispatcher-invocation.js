import { spawn } from "node:child_process";

import { isRecord } from "./payload-translation.js";

const hookDispatcherPath = "@opencodeHookDispatcher@";

export const hookDispatchers = {
  preToolUse: {
    filename: "pre-tool-use-dispatcher.py",
    timeoutMilliseconds: 5000,
  },
  postToolUse: {
    filename: "post-tool-use-dispatcher.py",
    timeoutMilliseconds: 15000,
  },
  sessionStart: {
    filename: "session-start-dispatcher.py",
    timeoutMilliseconds: 5000,
  },
  stop: { filename: "stop-dispatcher.py", timeoutMilliseconds: 15000 },
};

function parseDispatcherOutput(output, dispatcherFilename) {
  const trimmedOutput = output.trim();
  if (!trimmedOutput) {
    return {};
  }
  try {
    const parsedOutput = JSON.parse(trimmedOutput);
    if (!isRecord(parsedOutput)) {
      throw new Error(
        `OpenCode ${dispatcherFilename} hook returned invalid JSON`,
      );
    }
    return parsedOutput;
  } catch {
    throw new Error(
      `OpenCode ${dispatcherFilename} hook returned invalid JSON`,
    );
  }
}

function terminateHookDispatcher(childProcess) {
  try {
    if (process.platform !== "win32" && childProcess.pid) {
      process.kill(-childProcess.pid, "SIGTERM");
      return;
    }
    childProcess.kill();
  } catch {}
}

export function invokeHookDispatcher(dispatcher, payload) {
  return new Promise((resolve, reject) => {
    let childProcess;
    try {
      childProcess = spawn(hookDispatcherPath, [dispatcher.filename], {
        detached: process.platform !== "win32",
        stdio: ["pipe", "pipe", "pipe"],
      });
    } catch (error) {
      reject(error);
      return;
    }

    let standardOutput = "";
    let standardError = "";
    let completed = false;
    const complete = (callback, value) => {
      if (completed) {
        return;
      }
      completed = true;
      clearTimeout(timeoutIdentifier);
      callback(value);
    };
    const timeoutIdentifier = setTimeout(() => {
      terminateHookDispatcher(childProcess);
      complete(
        reject,
        new Error(
          `OpenCode ${dispatcher.filename} hook exceeded ${dispatcher.timeoutMilliseconds}ms`,
        ),
      );
    }, dispatcher.timeoutMilliseconds);

    childProcess.stdout.setEncoding("utf8");
    childProcess.stderr.setEncoding("utf8");
    childProcess.stdout.on("data", (chunk) => {
      standardOutput += chunk;
    });
    childProcess.stderr.on("data", (chunk) => {
      standardError += chunk;
    });
    childProcess.on("error", (error) => complete(reject, error));
    childProcess.stdin.on("error", (error) => complete(reject, error));
    childProcess.on("close", (exitCode, signal) => {
      if (exitCode !== 0) {
        const failureDetail =
          standardError.trim() || signal || `exit code ${exitCode}`;
        complete(
          reject,
          new Error(
            `OpenCode ${dispatcher.filename} hook failed: ${failureDetail}`,
          ),
        );
        return;
      }
      try {
        complete(
          resolve,
          parseDispatcherOutput(standardOutput, dispatcher.filename),
        );
      } catch (error) {
        complete(reject, error);
      }
    });
    childProcess.stdin.end(JSON.stringify(payload));
  });
}
