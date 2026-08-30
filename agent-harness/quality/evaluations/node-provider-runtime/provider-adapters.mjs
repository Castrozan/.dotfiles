const CLAUDE_READ_TOOLS = ["Read", "Glob", "Grep"];

const OPENCODE_READ_TOOLS = ["read", "grep", "glob", "list"];

const OPENCODE_TOOL_STATES = {
  read: true,
  grep: true,
  glob: true,
  list: true,
  bash: false,
  edit: false,
  write: false,
  patch: false,
  todowrite: false,
  todoread: false,
  webfetch: false,
  question: false,
  skill: false,
  lsp: false,
};

const OPENCODE_DENIED_PERMISSIONS = {
  edit: "deny",
  bash: "deny",
  webfetch: "deny",
  doom_loop: "deny",
  external_directory: "deny",
};

const NO_TOOLS_CODEX_ERROR =
  "codex-sdk adapter cannot enforce no_tools: the Codex SDK thread has no supported path to disable agent tool use, so the request is rejected instead of running with tools enabled";

export function claudeQueryOptions(invocation) {
  const tools = invocation.no_tools ? [] : CLAUDE_READ_TOOLS;
  const options = {
    cwd: invocation.working_directory,
    permissionMode: "dontAsk",
    tools,
    allowedTools: tools,
  };
  const binary = process.env.AGENT_EVAL_CLAUDE_BINARY;
  if (binary) options.pathToClaudeCodeExecutable = binary;
  if (invocation.model) options.model = invocation.model;
  if (invocation.system_prompt) options.systemPrompt = invocation.system_prompt;
  return options;
}

export function codexOptions() {
  const options = {};
  const binary = process.env.AGENT_EVAL_CODEX_BINARY;
  if (binary) options.codexPathOverride = binary;
  return options;
}

export function codexThreadOptions(invocation) {
  const options = {
    sandboxMode: "read-only",
    approvalPolicy: "never",
    networkAccessEnabled: false,
    webSearchEnabled: false,
    webSearchMode: "disabled",
    workingDirectory: invocation.working_directory,
    skipGitRepoCheck: true,
  };
  if (invocation.model) options.model = invocation.model;
  return options;
}

export function codexInput(invocation) {
  if (!invocation.system_prompt) return invocation.prompt;
  return `${invocation.system_prompt}\n\n${invocation.prompt}`;
}

export function openCodeConfig(invocation) {
  if (invocation.no_tools) {
    return {
      tools: Object.fromEntries(
        Object.keys(OPENCODE_TOOL_STATES).map((tool) => [tool, false]),
      ),
      permission: { ...OPENCODE_DENIED_PERMISSIONS },
    };
  }
  return {
    tools: { ...OPENCODE_TOOL_STATES },
    permission: { ...OPENCODE_DENIED_PERMISSIONS },
  };
}

export function openCodeToolSelection(availableTools, noTools) {
  return Object.fromEntries(
    availableTools.map((tool) => [
      tool,
      !noTools && OPENCODE_READ_TOOLS.includes(tool),
    ]),
  );
}

export function splitOpenCodeModel(model) {
  const separator = model.indexOf("/");
  if (separator <= 0 || separator === model.length - 1) {
    throw new Error(`openCode model "${model}" must be "provider/model"`);
  }
  return {
    providerID: model.slice(0, separator),
    modelID: model.slice(separator + 1),
  };
}

export function openCodePromptBody(invocation, tools) {
  const body = {
    parts: [{ type: "text", text: invocation.prompt }],
    tools,
  };
  if (invocation.system_prompt) body.system = invocation.system_prompt;
  if (invocation.model) body.model = splitOpenCodeModel(invocation.model);
  return body;
}

export function collectOpenCodeTextParts(parts) {
  return parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n");
}

export function normalizeRequestError(error) {
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (error && typeof error === "object") {
    const detail = error.detail ?? error.message ?? error.title;
    if (detail) return String(detail);
    return JSON.stringify(error);
  }
  return String(error);
}

export function validationError(invocation) {
  if (invocation.no_tools && invocation.harness === "codex") {
    return NO_TOOLS_CODEX_ERROR;
  }
  return null;
}
