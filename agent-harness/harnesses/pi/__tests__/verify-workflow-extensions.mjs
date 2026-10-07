import assert from "node:assert/strict";
import { copyFileSync, mkdtempSync, mkdirSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [modules, loopGuard, guardConfiguration] = process.argv.slice(2);
const root = mkdtempSync(join(tmpdir(), "pi-workflow-check-"));
const profile = join(root, "agent");
process.env.HOME = root;
process.env.PI_AGENT_DIR = profile;
process.env.PI_CODING_AGENT_DIR = profile;
mkdirSync(join(profile, "extensions"), { recursive: true });
mkdirSync(join(root, ".pi"));
symlinkSync(loopGuard, join(profile, "extensions/loop-guard"));
copyFileSync(guardConfiguration, join(root, ".pi/loop-guard.json"));
const { createAgentSession, SessionManager } = await import(
  pathToFileURL(join(modules, "@earendil-works/pi-coding-agent/dist/index.js"))
);
const { session, extensionsResult } = await createAgentSession({
  cwd: root,
  agentDir: profile,
  sessionManager: SessionManager.inMemory(root),
});
try {
  await session.bindExtensions({});
  assert.deepEqual(extensionsResult.errors, []);
  const runner = session.extensionRunner;
  const commands = runner
    .getRegisteredCommands()
    .map((command) => command.name);
  assert(!commands.includes("mode"));
  assert(commands.includes("loop-guard"));
  const call = (toolName, input) =>
    runner.emitToolCall({
      type: "tool_call",
      toolCallId: "probe",
      toolName,
      input,
    });
  for (const tool of ["read", "write", "edit", "bash"]) {
    assert(session.getActiveToolNames().includes(tool));
    assert.equal(
      (await call(tool, { path: "source.py", command: "pwd" }))?.block,
      undefined,
      tool,
    );
  }
  await runner.emit({ type: "agent_start" });
  for (let index = 0; index < 4; index++) {
    assert.equal(
      (
        await call("edit", {
          path: "source.py",
          edits: [{ oldText: String(index), newText: String(index + 1) }],
        })
      )?.block,
      undefined,
    );
    assert.equal(
      (await call("bash", { command: "python -m unittest" }))?.block,
      undefined,
    );
  }
  await runner.emit({ type: "agent_settled" });
  await runner.emit({ type: "agent_start" });
  assert.equal((await call("bash", { command: "false" }))?.block, undefined);
  assert.equal((await call("bash", { command: "false" }))?.block, undefined);
  const repeated = await call("bash", { command: "false" });
  assert.equal(repeated?.block, true);
  assert.equal(repeated?.terminate, true);
  await runner.emit({ type: "agent_settled" });
  await runner.emit({ type: "agent_start" });
  assert.equal((await call("bash", { command: "false" }))?.block, undefined);
  await runner.emit({ type: "agent_settled" });
  console.log(
    "Native tools, productive edit/test cycles, repetition stop and reset passed",
  );
} finally {
  await session.extensionRunner.emit({ type: "session_shutdown" });
  session.dispose();
}
