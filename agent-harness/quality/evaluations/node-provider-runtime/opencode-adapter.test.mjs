import { test } from "node:test";
import assert from "node:assert/strict";
import {
  collectOpenCodeTextParts,
  openCodeConfig,
  openCodeMessageOutcome,
  openCodeSessionInput,
  splitOpenCodeModel,
} from "./provider-adapters.mjs";

function invocation(overrides = {}) {
  return {
    prompt: "respond",
    working_directory: "/tmp",
    no_tools: false,
    ...overrides,
  };
}

function decision(configuration, action) {
  return configuration.agents["agent-eval"].permissions.findLast(
    (rule) => rule.action === action || rule.action === "*",
  ).effect;
}

test("read-only evaluation permits reads and denies mutating and unknown tools", () => {
  const configuration = openCodeConfig(invocation());
  for (const tool of ["read", "grep", "glob", "list"])
    assert.equal(decision(configuration, tool), "allow");
  for (const tool of [
    "shell",
    "write",
    "edit",
    "patch",
    "webfetch",
    "future_write_tool",
  ])
    assert.equal(decision(configuration, tool), "deny");
});

test("no_tools denies all existing and future tools", () => {
  const configuration = openCodeConfig(invocation({ no_tools: true }));
  for (const tool of ["read", "shell", "future_tool"])
    assert.equal(decision(configuration, tool), "deny");
});

test("the dedicated agent carries the system prompt and turn bound", () => {
  const request = invocation({ system_prompt: "SYSTEM", max_turns: 3 });
  const agent = openCodeConfig(request).agents["agent-eval"];
  assert.equal(agent.system, "SYSTEM");
  assert.equal(agent.steps, 3);
  assert.equal(openCodeSessionInput(request).agent, "agent-eval");
});

test("model selection preserves provider, nested model ID and reasoning variant", () => {
  assert.deepEqual(splitOpenCodeModel("provider/model/name#max"), {
    providerID: "provider",
    id: "model/name",
    variant: "max",
  });
  for (const model of ["model", "/model", "provider/"])
    assert.throws(() => splitOpenCodeModel(model), /provider\/model/);
});

test("session creation selects workspace, agent and optional model", () => {
  assert.deepEqual(
    openCodeSessionInput(invocation({ model: "anthropic/claude" })),
    {
      location: { directory: "/tmp" },
      agent: "agent-eval",
      model: { providerID: "anthropic", id: "claude" },
    },
  );
  assert.equal(openCodeSessionInput(invocation()).model, undefined);
});

test("only the last assistant message contributes output and tokens", () => {
  assert.deepEqual(
    openCodeMessageOutcome([
      { type: "assistant", content: [{ type: "text", text: "Earlier" }] },
      { type: "user", text: "Request" },
      {
        type: "assistant",
        tokens: {
          input: 13,
          output: 7,
          reasoning: 2,
          cache: { read: 5, write: 3 },
        },
        content: [
          { type: "text", text: "first" },
          { type: "tool" },
          { type: "text", text: "second" },
        ],
      },
    ]),
    {
      output: "first\nsecond",
      error: null,
      usage: {
        input_tokens: 13,
        cached_input_tokens: 5,
        cache_write_input_tokens: 3,
        output_tokens: 7,
        reasoning_output_tokens: 2,
      },
    },
  );
  assert.equal(collectOpenCodeTextParts([]), "");
});

test("failed or missing assistant messages fail the evaluation", () => {
  assert.match(
    openCodeMessageOutcome([]).error,
    /without an assistant message/,
  );
  assert.deepEqual(
    openCodeMessageOutcome([
      { type: "assistant", error: { message: "provider failed" } },
    ]),
    { output: null, error: "provider failed" },
  );
});
