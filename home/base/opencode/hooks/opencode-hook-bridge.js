import { spawn } from "node:child_process";

const hookDispatcherPath = "@opencodeHookDispatcher@";

const hookDispatchers = {
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
  userPromptSubmit: {
    filename: "user-prompt-submit-dispatcher.py",
    timeoutMilliseconds: 2000,
  },
};

const canonicalToolNames = {
  bash: "Bash",
  edit: "Edit",
  skill: "Skill",
  task: "Agent",
  webfetch: "WebFetch",
  write: "Write",
};

const opencodeArgumentNames = {
  file_path: "filePath",
  new_string: "newString",
  old_string: "oldString",
  patch_text: "patchText",
};

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function snakeCaseKey(key) {
  return key.replace(/[A-Z]/g, (character) => `_${character.toLowerCase()}`);
}

function normalizeToolInput(value) {
  if (Array.isArray(value)) {
    return value.map(normalizeToolInput);
  }
  if (!isRecord(value)) {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value).map(([key, child]) => [
      snakeCaseKey(key),
      normalizeToolInput(child),
    ]),
  );
}

function opencodeToolInput(value) {
  if (Array.isArray(value)) {
    return value.map(opencodeToolInput);
  }
  if (!isRecord(value)) {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value).map(([key, child]) => [
      opencodeArgumentNames[key] ?? key,
      opencodeToolInput(child),
    ]),
  );
}

function canonicalToolName(toolName) {
  return canonicalToolNames[toolName] ?? toolName;
}

function toolInputForDispatcher(toolName, toolInput) {
  const normalizedInput = normalizeToolInput(toolInput);
  if (
    canonicalToolName(toolName) === "apply_patch" &&
    isRecord(normalizedInput) &&
    typeof normalizedInput.patch_text === "string"
  ) {
    return normalizedInput.patch_text;
  }
  if (
    canonicalToolName(toolName) !== "Skill" ||
    !isRecord(normalizedInput) ||
    typeof normalizedInput.name !== "string"
  ) {
    return normalizedInput;
  }
  const { name, ...remainingInput } = normalizedInput;
  return { ...remainingInput, skill: name };
}

function hookPayload(eventName, sessionID, directory, additionalFields = {}) {
  return {
    hook_event_name: eventName,
    session_id: sessionID ?? "",
    cwd: directory,
    ...additionalFields,
  };
}

function toolHookPayload(eventName, input, args, directory) {
  return hookPayload(eventName, input.sessionID, directory, {
    tool_name: canonicalToolName(input.tool),
    tool_input: toolInputForDispatcher(input.tool, args),
  });
}

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

function invokeHookDispatcher(dispatcher, payload) {
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

function terminateHookDispatcher(childProcess) {
  try {
    if (process.platform !== "win32" && childProcess.pid) {
      process.kill(-childProcess.pid, "SIGTERM");
      return;
    }
    childProcess.kill();
  } catch {}
}

function hookSpecificOutput(dispatcherOutput) {
  return isRecord(dispatcherOutput.hookSpecificOutput)
    ? dispatcherOutput.hookSpecificOutput
    : {};
}

function additionalContext(dispatcherOutput) {
  const context = hookSpecificOutput(dispatcherOutput).additionalContext;
  return typeof context === "string" && context ? context : "";
}

function dispatcherMessages(dispatcherOutput) {
  const messages = [
    dispatcherOutput.systemMessage,
    dispatcherOutput.reason,
    additionalContext(dispatcherOutput),
  ].filter((message) => typeof message === "string" && message);
  return [...new Set(messages)];
}

function appendToolOutputMessage(toolOutput, dispatcherOutput) {
  const messages = dispatcherMessages(dispatcherOutput);
  if (messages.length === 0) {
    return;
  }
  const existingOutput =
    typeof toolOutput.output === "string" ? toolOutput.output : "";
  toolOutput.output = [existingOutput, ...messages]
    .filter(Boolean)
    .join("\n\n");
}

function appendPromptContext(parts, context) {
  if (!context || !Array.isArray(parts)) {
    return;
  }
  const textPart = parts.find(
    (part) =>
      isRecord(part) && part.type === "text" && typeof part.text === "string",
  );
  if (!textPart) {
    return;
  }
  textPart.text = [textPart.text, context].filter(Boolean).join("\n\n");
}

function containsTextPart(parts) {
  return (
    Array.isArray(parts) &&
    parts.some(
      (part) =>
        isRecord(part) && part.type === "text" && typeof part.text === "string",
    )
  );
}

function applyUpdatedToolInput(toolOutput, updatedInput) {
  const translatedInput = opencodeToolInput(updatedInput);
  if (!isRecord(toolOutput.args)) {
    toolOutput.args = translatedInput;
    return;
  }
  for (const key of Object.keys(toolOutput.args)) {
    delete toolOutput.args[key];
  }
  Object.assign(toolOutput.args, translatedInput);
}

function preToolUseDenial(dispatcherOutput) {
  const specificOutput = hookSpecificOutput(dispatcherOutput);
  if (!new Set(["block", "deny"]).has(specificOutput.permissionDecision)) {
    return "";
  }
  return (
    specificOutput.permissionDecisionReason ||
    dispatcherOutput.reason ||
    dispatcherOutput.systemMessage ||
    "OpenCode blocked this tool call."
  );
}

function blockingDecisionReason(dispatcherOutput) {
  if (!new Set(["block", "deny"]).has(dispatcherOutput.decision)) {
    return "";
  }
  return (
    dispatcherOutput.reason ||
    dispatcherOutput.systemMessage ||
    "OpenCode blocked this tool result."
  );
}

export async function OpenCodeHookBridge({ directory } = {}) {
  const workingDirectory =
    typeof directory === "string" && directory ? directory : process.cwd();

  return {
    "tool.execute.before": async (input, output) => {
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.preToolUse,
        toolHookPayload("PreToolUse", input, output.args, workingDirectory),
      );
      const updatedInput = hookSpecificOutput(dispatcherOutput).updatedInput;
      if (isRecord(updatedInput)) {
        applyUpdatedToolInput(output, updatedInput);
      }
      const denial = preToolUseDenial(dispatcherOutput);
      if (denial) {
        throw new Error(denial);
      }
    },
    "tool.execute.after": async (input, output) => {
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.postToolUse,
        toolHookPayload("PostToolUse", input, input.args, workingDirectory),
      );
      const postToolBlock = blockingDecisionReason(dispatcherOutput);
      if (postToolBlock) {
        throw new Error(postToolBlock);
      }
      appendToolOutputMessage(output, dispatcherOutput);
      const turnReviewOutput = await invokeHookDispatcher(
        hookDispatchers.stop,
        hookPayload("Stop", input.sessionID, workingDirectory),
      );
      const turnReviewBlock = blockingDecisionReason(turnReviewOutput);
      if (turnReviewBlock) {
        throw new Error(turnReviewBlock);
      }
      appendToolOutputMessage(output, turnReviewOutput);
    },
    "chat.message": async (input, output) => {
      if (!containsTextPart(output.parts)) {
        return;
      }
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.userPromptSubmit,
        hookPayload("UserPromptSubmit", input.sessionID, workingDirectory),
      );
      appendPromptContext(output.parts, additionalContext(dispatcherOutput));
    },
    "experimental.session.compacting": async (input, output) => {
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.sessionStart,
        hookPayload("SessionStart", input.sessionID, workingDirectory, {
          source: "compact",
        }),
      );
      const context = additionalContext(dispatcherOutput);
      if (context) {
        output.context.push(context);
      }
    },
  };
}
