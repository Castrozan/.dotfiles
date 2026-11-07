import { test } from "node:test";
import assert from "node:assert/strict";

import { claudeQueryOptions, codexOptions } from "./provider-adapters.mjs";

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

test("an isolated claude judge loads no filesystem settings", () => {
  assert.deepEqual(
    claudeQueryOptions(invocation({ isolated_context: true })).settingSources,
    [],
  );
  assert.equal(claudeQueryOptions(invocation()).settingSources, undefined);
});

test("an isolated codex judge runs without hooks or project instructions", () => {
  const options = codexOptions(
    invocation({ harness: "codex", no_tools: true, isolated_context: true }),
  );
  assert.equal(options.config.features.hooks, false);
  assert.equal(options.config.features.multi_agent, false);
  assert.equal(options.config.project_doc_max_bytes, 0);
  assert.equal(
    codexOptions(invocation({ harness: "codex" })).config,
    undefined,
  );
});
