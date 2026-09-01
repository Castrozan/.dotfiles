import { test } from "node:test";
import assert from "node:assert/strict";

import {
  claudeQueryOptions,
  claudeResultOutcome,
  codexInput,
  codexOptions,
  codexThreadOptions,
} from "./provider-adapters.mjs";

function invocation(overrides = {}) {
  return {
    harness: "claude",
    prompt: "respond",
    model: null,
    system_prompt: null,
    working_directory: "/tmp",
    timeout: 120,
    max_turns: null,
    no_tools: false,
    ...overrides,
  };
}

test("claude maps cwd, model, turn limit, system prompt, dontAsk, and the binary path", () => {
  process.env.AGENT_EVAL_CLAUDE_BINARY = "/bin/claude";
  try {
    const options = claudeQueryOptions(
      invocation({
        system_prompt: "SYS",
        model: "sonnet",
        max_turns: 2,
        working_directory: "/eval/dir",
      }),
    );
    assert.equal(options.cwd, "/eval/dir");
    assert.equal(options.permissionMode, "dontAsk");
    assert.equal(options.pathToClaudeCodeExecutable, "/bin/claude");
    assert.equal(options.model, "sonnet");
    assert.equal(options.maxTurns, 2);
    assert.equal(options.systemPrompt, "SYS");
    assert.deepEqual(options.tools, ["Read", "Glob", "Grep"]);
    assert.deepEqual(options.allowedTools, ["Read", "Glob", "Grep"]);
  } finally {
    delete process.env.AGENT_EVAL_CLAUDE_BINARY;
  }
});

test("claude omits the binary path when the environment does not set it", () => {
  delete process.env.AGENT_EVAL_CLAUDE_BINARY;
  const options = claudeQueryOptions(invocation());
  assert.equal(options.pathToClaudeCodeExecutable, undefined);
});

test("claude no_tools forbids every tool", () => {
  const options = claudeQueryOptions(invocation({ no_tools: true }));
  assert.deepEqual(options.tools, []);
  assert.deepEqual(options.allowedTools, []);
});

test("claude with no model or system prompt omits both", () => {
  const options = claudeQueryOptions(invocation());
  assert.equal(options.model, undefined);
  assert.equal(options.systemPrompt, undefined);
});

test("claude preserves the result text from an error result", () => {
  assert.deepEqual(
    claudeResultOutcome({
      type: "result",
      subtype: "success",
      is_error: true,
      result: "You've hit your session limit",
    }),
    { output: null, error: "You've hit your session limit" },
  );
});

test("claude returns successful result text as output", () => {
  assert.deepEqual(
    claudeResultOutcome({
      type: "result",
      subtype: "success",
      is_error: false,
      result: "OK",
    }),
    { output: "OK", error: null },
  );
});

test("claude normalizes cumulative model usage", () => {
  assert.deepEqual(
    claudeResultOutcome({
      type: "result",
      subtype: "success",
      is_error: false,
      result: "OK",
      modelUsage: {
        "claude-sonnet": {
          inputTokens: 10,
          outputTokens: 5,
          cacheReadInputTokens: 4,
          cacheCreationInputTokens: 2,
        },
        "claude-haiku": {
          inputTokens: 3,
          outputTokens: 1,
          cacheReadInputTokens: 2,
          cacheCreationInputTokens: 1,
        },
      },
    }),
    {
      output: "OK",
      error: null,
      usage: {
        input_tokens: 13,
        cached_input_tokens: 6,
        cache_write_input_tokens: 3,
        output_tokens: 6,
        reasoning_output_tokens: 0,
      },
    },
  );
});

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

test("codex maps the binary, thread options, model, and reasoning effort", () => {
  process.env.AGENT_EVAL_CODEX_BINARY = "/bin/codex";
  try {
    const options = codexOptions(invocation());
    assert.equal(options.codexPathOverride, "/bin/codex");
  } finally {
    delete process.env.AGENT_EVAL_CODEX_BINARY;
  }
  const threadOptions = codexThreadOptions(
    invocation({
      model: "gpt-5",
      working_directory: "/eval/dir",
      model_reasoning_effort: "high",
    }),
  );
  assert.equal(threadOptions.sandboxMode, "read-only");
  assert.equal(threadOptions.approvalPolicy, "never");
  assert.equal(threadOptions.networkAccessEnabled, false);
  assert.equal(threadOptions.webSearchEnabled, false);
  assert.equal(threadOptions.webSearchMode, "disabled");
  assert.equal(threadOptions.skipGitRepoCheck, true);
  assert.equal(threadOptions.workingDirectory, "/eval/dir");
  assert.equal(threadOptions.model, "gpt-5");
  assert.equal(threadOptions.modelReasoningEffort, "high");
});

test("codex thread options omit reasoning effort when not given", () => {
  const threadOptions = codexThreadOptions(invocation({ model: "gpt-5" }));
  assert.equal(threadOptions.modelReasoningEffort, undefined);
});

test("codex routes system instructions through vendor config", () => {
  delete process.env.AGENT_EVAL_CODEX_BINARY;
  assert.deepEqual(codexOptions(invocation()), {});
  assert.deepEqual(codexOptions(invocation({ system_prompt: "SYS" })), {
    config: { developer_instructions: "SYS" },
  });
  assert.equal(codexInput(invocation({ system_prompt: "SYS" })), "respond");
  assert.equal(codexInput(invocation()), "respond");
});

test("codex no_tools supplies config overrides that disable agent tool use", () => {
  delete process.env.AGENT_EVAL_CODEX_BINARY;
  const options = codexOptions(
    invocation({ no_tools: true, system_prompt: "SYS" }),
  );
  assert.deepEqual(options.config, {
    developer_instructions: "SYS",
    apps: { _default: { enabled: false } },
    mcp_servers: {},
    tools: { view_image: false, web_search: false },
    features: CODEX_NO_TOOLS_FEATURES,
  });
});

test("codex no_tools keeps the binary override and config overrides", () => {
  process.env.AGENT_EVAL_CODEX_BINARY = "/bin/codex";
  try {
    const options = codexOptions(invocation({ no_tools: true }));
    assert.equal(options.codexPathOverride, "/bin/codex");
    assert.equal(options.config.features.apps, false);
  } finally {
    delete process.env.AGENT_EVAL_CODEX_BINARY;
  }
});
