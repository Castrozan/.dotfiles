import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, symlinkSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [modules, extension] = process.argv.slice(2);
const root = mkdtempSync(join(tmpdir(), "pi-native-reply-guard-"));
const profile = join(root, "agent");
process.env.HOME = root;
process.env.PI_AGENT_DIR = profile;
process.env.PI_CODING_AGENT_DIR = profile;
mkdirSync(join(profile, "extensions"), { recursive: true });
symlinkSync(extension, join(profile, "extensions/human-facing-reply-guard.js"));
const requests = [];
let reply = "| Result |\n| --- |\n| Passed |";
const server = createServer(async (request, response) => {
  let body = "";
  for await (const chunk of request) body += chunk;
  requests.push(JSON.parse(body));
  response.writeHead(200, { "Content-Type": "text/event-stream" });
  for (const [delta, finishReason] of [
    [{ role: "assistant", content: reply }, null],
    [{}, "stop"],
  ]) {
    response.write(
      `data: ${JSON.stringify({
        id: "chatcmpl-reply-guard",
        object: "chat.completion.chunk",
        created: 1,
        model: "fixture",
        choices: [{ index: 0, delta, finish_reason: finishReason }],
      })}\n\n`,
    );
  }
  response.end("data: [DONE]\n\n");
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const { createAgentSession, ModelRuntime, SessionManager } = await import(
  pathToFileURL(join(modules, "@earendil-works/pi-coding-agent/dist/index.js"))
);
const modelRuntime = await ModelRuntime.create({
  authPath: join(profile, "auth.json"),
  modelsPath: null,
  refreshOnCreate: false,
});
modelRuntime.registerProvider("acceptance", {
  api: "openai-completions",
  baseUrl: `http://127.0.0.1:${server.address().port}/v1`,
  apiKey: "native-fixture",
  models: [
    {
      id: "fixture",
      name: "Native fixture",
      reasoning: false,
      input: ["text"],
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
      contextWindow: 131072,
      maxTokens: 2048,
    },
  ],
});
const { session, extensionsResult } = await createAgentSession({
  cwd: root,
  agentDir: profile,
  modelRuntime,
  model: modelRuntime.getModel("acceptance", "fixture"),
  sessionManager: SessionManager.inMemory(root),
});
const errors = [];
let settledTurns = 0;
const subscribers = new Set();
const unsubscribe = session.subscribe((event) => {
  if (event.type === "agent_settled") {
    settledTurns++;
    for (const subscriber of subscribers) subscriber();
  }
});
function awaitSettledTurns(target) {
  if (settledTurns >= target) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      subscribers.delete(check);
      reject(
        new Error(`Expected ${target} settled turns, observed ${settledTurns}`),
      );
    }, 5000);
    const check = () => {
      if (settledTurns < target) return;
      clearTimeout(timer);
      subscribers.delete(check);
      resolve();
    };
    subscribers.add(check);
  });
}
const corrections = () =>
  session.messages.filter(
    (message) =>
      message.role === "custom" &&
      message.customType === "human-facing-reply-format-guard",
  );
try {
  await session.bindExtensions({ onError: (error) => errors.push(error) });
  assert.deepEqual(extensionsResult.errors, []);
  assert.equal(extensionsResult.extensions.length, 1);
  const baseline = await session.extensionRunner.emitToolCall({
    type: "tool_call",
    toolCallId: "unsupported-pretool",
    toolName: "bash",
    input: { command: "pytest -q" },
  });
  assert.equal(baseline?.block, undefined);
  await session.prompt("Report the first result.");
  await awaitSettledTurns(2);
  assert.equal(requests.length, 2);
  assert.equal(corrections().length, 1);
  assert.equal(corrections()[0].display, false);
  assert.match(corrections()[0].content, /table|index/i);
  assert.match(JSON.stringify(requests[1].messages), /table|index/i);
  await session.prompt("Report the next result.");
  await awaitSettledTurns(4);
  assert.equal(requests.length, 4);
  assert.equal(corrections().length, 2);
  reply = "Ready.";
  await session.prompt("Confirm readiness.");
  await awaitSettledTurns(5);
  assert.equal(requests.length, 5);
  assert.equal(corrections().length, 2);
  assert.deepEqual(errors, []);
  console.log(
    "Native Stop correction, bounded continuation, user-turn reset and valid reply passed; PreToolUse unsupported",
  );
} finally {
  unsubscribe();
  await session.extensionRunner.emit({ type: "session_shutdown" });
  session.dispose();
  await new Promise((resolve) => server.close(resolve));
  rmSync(root, { recursive: true, force: true });
}
