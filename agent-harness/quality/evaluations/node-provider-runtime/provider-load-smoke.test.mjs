import { test } from "node:test";
import assert from "node:assert/strict";

import {
  claudeQueryOptions,
  codexThreadOptions,
  openCodeConfig,
  openCodePromptBody,
  validationError,
} from "./provider-adapters.mjs";
import { runSubjectInvocation } from "./provider-runtime.mjs";

const ALL_HARNESSES = ["claude", "codex", "opencode"];

const SDK_SYMBOLS = {
  "@anthropic-ai/claude-agent-sdk": "query",
  "@openai/codex-sdk": "Codex",
  "@opencode-ai/sdk": "createOpencode",
};

function representativeInvocation(harness) {
  return {
    harness,
    prompt: "respond",
    model: null,
    system_prompt: "base system prompt",
    working_directory: "/tmp",
    timeout: 120,
    no_tools: false,
  };
}

for (const moduleName of Object.keys(SDK_SYMBOLS)) {
  test(`sdk module ${moduleName} imports without a model call`, async () => {
    const sdk = await import(moduleName);
    assert.equal(typeof sdk[SDK_SYMBOLS[moduleName]], "function");
  });
}

for (const harness of ALL_HARNESSES) {
  test(`adapter options for harness ${harness} build without a model call`, () => {
    const invocation = representativeInvocation(harness);
    if (harness === "claude") {
      assert.equal(claudeQueryOptions(invocation).permissionMode, "dontAsk");
    } else if (harness === "codex") {
      assert.equal(codexThreadOptions(invocation).sandboxMode, "read-only");
    } else {
      assert.equal(openCodeConfig(invocation).tools.read, true);
      assert.equal(
        openCodePromptBody(invocation, {}).system,
        "base system prompt",
      );
    }
  });
}

test("codex no_tools request fails closed before any model call", async () => {
  const outcome = await runSubjectInvocation({
    ...representativeInvocation("codex"),
    no_tools: true,
  });
  assert.equal(outcome.output, null);
  assert.match(outcome.error, /cannot enforce no_tools/);
});

test("unknown harness is rejected without reaching a model call", async () => {
  const outcome = await runSubjectInvocation({
    harness: "unknown",
    prompt: "respond",
    result_file: "/tmp/unused.json",
  });
  assert.equal(outcome.output, null);
  assert.match(outcome.error, /unknown harness/);
});
