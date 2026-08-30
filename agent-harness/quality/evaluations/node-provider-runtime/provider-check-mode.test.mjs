import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const RUNTIME_ENTRY = fileURLToPath(
  new URL("./provider-runtime.mjs", import.meta.url),
);

const EXPECTED_PROVIDERS = [
  "claude:@anthropic-ai/claude-agent-sdk:function",
  "codex:@openai/codex-sdk:function",
  "opencode:@opencode-ai/sdk:function",
];

function runCheckMode(workingDirectory) {
  const resultFile = join(
    mkdtempSync(join(tmpdir(), "agent-eval-check-")),
    "result.json",
  );
  const request = JSON.stringify({ check: true, result_file: resultFile });
  execFileSync(process.execPath, [RUNTIME_ENTRY], {
    cwd: workingDirectory,
    input: request,
    stdio: ["pipe", "pipe", "pipe"],
  });
  const result = JSON.parse(readFileSync(resultFile, "utf8"));
  rmSync(join(resultFile, ".."), { recursive: true, force: true });
  return result;
}

test(
  "check mode anchors resolution to the packaged runtime and resolves every SDK adapter",
  { timeout: 60000 },
  () => {
    const unrelatedCwd = mkdtempSync(join(tmpdir(), "agent-eval-hostile-"));
    try {
      const result = runCheckMode(unrelatedCwd);
      assert.equal(result.error, null);
      assert.equal(result.output, null);
      assert.deepEqual(result.providers, EXPECTED_PROVIDERS);
      assert.equal(
        result.resolution_directory,
        result.runtime_directory,
        "SDK resolution must be anchored to the packaged runtime directory, not the subject cwd",
      );
      assert.notEqual(result.runtime_directory, unrelatedCwd);
    } finally {
      rmSync(unrelatedCwd, { recursive: true, force: true });
    }
  },
);
