import { test } from "node:test";
import assert from "node:assert/strict";

import {
  collectOpenCodeTextParts,
  openCodeConfig,
  openCodePromptBody,
  openCodeToolSelection,
  splitOpenCodeModel,
} from "./provider-adapters.mjs";

function invocation(overrides = {}) {
  return {
    harness: "opencode",
    prompt: "respond",
    model: null,
    system_prompt: null,
    working_directory: "/tmp",
    timeout: 120,
    no_tools: false,
    ...overrides,
  };
}

test("openCode config enables read tools and disables write, bash, and web tools", () => {
  const config = openCodeConfig(invocation());
  for (const readTool of ["read", "grep", "glob", "list"]) {
    assert.equal(config.tools[readTool], true);
  }
  for (const writeTool of ["bash", "edit", "write", "patch", "webfetch"]) {
    assert.equal(config.tools[writeTool], false);
  }
  assert.equal(config.permission.edit, "deny");
  assert.equal(config.permission.bash, "deny");
  assert.equal(config.permission.webfetch, "deny");
});

test("openCode no_tools disables every tool", () => {
  const config = openCodeConfig(invocation({ no_tools: true }));
  for (const tool of [
    "read",
    "grep",
    "glob",
    "list",
    "bash",
    "edit",
    "write",
    "patch",
    "webfetch",
  ]) {
    assert.equal(config.tools[tool], false);
  }
});

test("openCode splits the provider and model", () => {
  assert.deepEqual(splitOpenCodeModel("anthropic/claude-2"), {
    providerID: "anthropic",
    modelID: "claude-2",
  });
  assert.throws(() => splitOpenCodeModel("claude-2"), /"provider\/model"/);
  assert.throws(() => splitOpenCodeModel("/claude-2"), /"provider\/model"/);
  assert.throws(() => splitOpenCodeModel("anthropic/"), /"provider\/model"/);
});

test("openCode prompt body carries the prompt, system prompt, and model split", () => {
  const tools = { read: true, write: false };
  const body = openCodePromptBody(
    invocation({ system_prompt: "SYS", model: "anthropic/claude-2" }),
    tools,
  );
  assert.deepEqual(body.parts, [{ type: "text", text: "respond" }]);
  assert.equal(body.system, "SYS");
  assert.deepEqual(body.model, {
    providerID: "anthropic",
    modelID: "claude-2",
  });
  assert.deepEqual(body.tools, tools);
});

test("openCode prompt body without inputs carries only the prompt", () => {
  const body = openCodePromptBody(invocation(), {});
  assert.equal(body.system, undefined);
  assert.equal(body.model, undefined);
  assert.deepEqual(body.parts, [{ type: "text", text: "respond" }]);
});

test("openCode capability selection denies unknown tools", () => {
  const available = ["read", "grep", "bash", "future_write_tool"];
  assert.deepEqual(openCodeToolSelection(available, false), {
    read: true,
    grep: true,
    bash: false,
    future_write_tool: false,
  });
  assert.deepEqual(openCodeToolSelection(available, true), {
    read: false,
    grep: false,
    bash: false,
    future_write_tool: false,
  });
});

test("openCode text collection joins text parts and skips non-text parts", () => {
  assert.equal(
    collectOpenCodeTextParts([
      { type: "text", text: "first" },
      { type: "tool", tool: "bash" },
      { type: "text", text: "second" },
    ]),
    "first\nsecond",
  );
  assert.equal(collectOpenCodeTextParts([]), "");
});
