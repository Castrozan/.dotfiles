import {
  normalizeClaudeModelUsage,
  normalizeOpenCodeUsage,
} from "./provider-usage.mjs";

const CLAUDE_READ_TOOLS = ["Read", "Glob", "Grep"];

const OPENCODE_READ_TOOLS = ["read", "grep", "glob", "list"];

const CODEX_NO_TOOLS_FEATURES = {
  apps: false,
  browser_use: false,
  code_mode_host: false,
  computer_use: false,
  image_generation: false,
  multi_agent: false,
  plugins: false,
  shell_tool: false,
  unified_exec: false,
};

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
  _addClaudeOptionalOptions(options, invocation);
  return options;
}

function _addClaudeOptionalOptions(options, invocation) {
  if (invocation.model) options.model = invocation.model;
  if (invocation.max_turns) options.maxTurns = invocation.max_turns;
  if (invocation.system_prompt) options.systemPrompt = invocation.system_prompt;
}

export function claudeResultOutcome(message) {
  const errors = (message.errors ?? []).join("\n");
  const usage = normalizeClaudeModelUsage(message.modelUsage);
  if (message.is_error === true) return _claudeErrorOutcome(message, errors, usage);
  const outcome = { output: message.result, error: null };
  if (usage) outcome.usage = usage;
  return outcome;
}

function _claudeErrorOutcome(message, errors, usage) {
  const outcome = {
    output: null,
    error:
      errors ||
      message.result ||
      message.subtype ||
      "claude query returned an error result",
  };
  if (usage) outcome.usage = usage;
  return outcome;
}

export function codexOptions(invocation) {
  const options = {};
  const binary = process.env.AGENT_EVAL_CODEX_BINARY;
  if (binary) options.codexPathOverride = binary;
  const config = {};
  if (invocation.system_prompt) {
    config.developer_instructions = invocation.system_prompt;
  }
  if (invocation.no_tools) {
    config.apps = { _default: { enabled: false } };
    config.mcp_servers = {};
    config.tools = { view_image: false, web_search: false };
    config.features = { ...CODEX_NO_TOOLS_FEATURES };
  }
  if (Object.keys(config).length > 0) options.config = config;
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
  if (invocation.model_reasoning_effort) {
    options.modelReasoningEffort = invocation.model_reasoning_effort;
  }
  return options;
}

export function codexInput(invocation) {
  return invocation.prompt;
}

export function openCodeConfig(invocation) {
  const permissions = [{ action: "*", resource: "*", effect: "deny" }];
  if (!invocation.no_tools) {
    permissions.push(
      ...OPENCODE_READ_TOOLS.map((action) => ({
        action,
        resource: "*",
        effect: "allow",
      })),
    );
  }
  const agent = { mode: "primary", permissions };
  if (invocation.system_prompt) agent.system = invocation.system_prompt;
  if (invocation.max_turns) agent.steps = invocation.max_turns;
  return { agents: { "agent-eval": agent } };
}

export function splitOpenCodeModel(model) {
  const separator = model.indexOf("/");
  if (separator <= 0 || separator === model.length - 1) {
    throw new Error(`openCode model "${model}" must be "provider/model"`);
  }
  const [id, variant] = model.slice(separator + 1).split("#");
  return {
    providerID: model.slice(0, separator),
    id,
    ...(variant ? { variant } : {}),
  };
}

export function openCodeSessionInput(invocation) {
  return {
    location: { directory: invocation.working_directory },
    agent: "agent-eval",
    ...(invocation.model
      ? { model: splitOpenCodeModel(invocation.model) }
      : {}),
  };
}

export function collectOpenCodeTextParts(parts) {
  return parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n");
}

export function openCodeMessageOutcome(messages) {
  const message = messages.findLast((item) => item.type === "assistant");
  if (!message)
    return {
      output: null,
      error: "opencode session ended without an assistant message",
    };
  if (message.error)
    return { output: null, error: normalizeRequestError(message.error) };
  return {
    output: collectOpenCodeTextParts(message.content),
    error: null,
    usage: normalizeOpenCodeUsage(message.tokens),
  };
}

export function normalizeRequestError(error) {
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (error && typeof error === "object") return _normalizeObjectRequestError(error);
  return String(error);
}

function _normalizeObjectRequestError(error) {
  const detail = error.detail ?? error.message ?? error.title;
  if (detail) return String(detail);
  return JSON.stringify(error);
}
