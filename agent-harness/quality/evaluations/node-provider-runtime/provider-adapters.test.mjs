import { test } from "node:test";
import assert from "node:assert/strict";

import {
  claudeQueryOptions,
  claudeResultOutcome,
  codexInput,
  codexOptions,
  codexThreadOptions,
  validationError,
} from "./provider-adapters.mjs";

function invocation(overrides = {}) {
  return {
    harness: "claude",
    prompt: "respond",
    model: null,
    system_prompt: null,
    working_directory: "/tmp",
    timeout: 120,
    no_tools: false,
    ...overrides,
  };
}

test("claude maps cwd, model, system prompt, dontAsk, and the binary path", () => {
  process.env.AGENT_EVAL_CLAUDE_BINARY = "/bin/claude";
  try {
    const options = claudeQueryOptions(
      invocation({
        system_prompt: "SYS",
        model: "sonnet",
        working_directory: "/eval/dir",
      }),
    );
    assert.equal(options.cwd, "/eval/dir");
    assert.equal(options.permissionMode, "dontAsk");
    assert.equal(options.pathToClaudeCodeExecutable, "/bin/claude");
    assert.equal(options.model, "sonnet");
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

test("codex maps the binary, thread options, and model", () => {
  process.env.AGENT_EVAL_CODEX_BINARY = "/bin/codex";
  try {
    const options = codexOptions();
    assert.equal(options.codexPathOverride, "/bin/codex");
  } finally {
    delete process.env.AGENT_EVAL_CODEX_BINARY;
  }
  const threadOptions = codexThreadOptions(
    invocation({ model: "gpt-5", working_directory: "/eval/dir" }),
  );
  assert.equal(threadOptions.sandboxMode, "read-only");
  assert.equal(threadOptions.approvalPolicy, "never");
  assert.equal(threadOptions.networkAccessEnabled, false);
  assert.equal(threadOptions.webSearchEnabled, false);
  assert.equal(threadOptions.webSearchMode, "disabled");
  assert.equal(threadOptions.skipGitRepoCheck, true);
  assert.equal(threadOptions.workingDirectory, "/eval/dir");
  assert.equal(threadOptions.model, "gpt-5");
});

test("codex omits the binary override and prefixes the system prompt", () => {
  delete process.env.AGENT_EVAL_CODEX_BINARY;
  assert.deepEqual(codexOptions(), {});
  assert.equal(
    codexInput(invocation({ system_prompt: "SYS" })),
    "SYS\n\nrespond",
  );
  assert.equal(codexInput(invocation()), "respond");
});

test("codex no_tools fails closed", () => {
  const closedError = validationError({
    harness: "codex",
    no_tools: true,
  });
  assert.ok(closedError);
  assert.match(closedError, /cannot enforce no_tools/);
});

test("non-codex no_tools is not rejected by the edge", () => {
  for (const harness of ["claude", "opencode"]) {
    assert.equal(validationError({ harness, no_tools: true }), null);
  }
});
