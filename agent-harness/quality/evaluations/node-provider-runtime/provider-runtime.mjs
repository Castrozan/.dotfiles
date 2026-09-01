import { realpathSync, readFileSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { validationError } from "./provider-adapters.mjs";
import { runnerFor } from "./provider-runners.mjs";

const CHECK_RESOLUTIONS = [
  ["claude", "@anthropic-ai/claude-agent-sdk", "query"],
  ["codex", "@openai/codex-sdk", "Codex"],
  ["opencode", "@opencode-ai/sdk", "createOpencode"],
];

const RUNTIME_DIRECTORY = dirname(fileURLToPath(import.meta.url));

process.chdir(RUNTIME_DIRECTORY);

function writeResult(resultFile, result) {
  writeFileSync(resultFile, JSON.stringify(result), "utf8");
}

export async function runSubjectInvocation(invocation) {
  const closedError = validationError(invocation);
  if (closedError) {
    return { output: null, error: closedError };
  }
  const runner = runnerFor(invocation.harness);
  if (!runner) {
    return { output: null, error: `unknown harness: ${invocation.harness}` };
  }
  return runner(invocation);
}

export async function runResolutionCheck() {
  const providers = [];
  for (const [harness, moduleName, symbol] of CHECK_RESOLUTIONS) {
    const sdk = await import(moduleName);
    providers.push(`${harness}:${moduleName}:${typeof sdk[symbol]}`);
  }
  return {
    providers,
    resolution_directory: process.cwd(),
    runtime_directory: RUNTIME_DIRECTORY,
    error: null,
  };
}

async function main() {
  const requestText = readFileSync(0, "utf8");
  const request = JSON.parse(requestText);
  const result = {
    output: null,
    error: null,
    providers: null,
  };
  try {
    if (request.check) {
      const outcome = await runResolutionCheck();
      result.providers = outcome.providers;
      result.resolution_directory = outcome.resolution_directory;
      result.runtime_directory = outcome.runtime_directory;
      result.error = outcome.error;
    } else {
      const outcome = await runSubjectInvocation(request);
      result.output = outcome.output;
      result.error = outcome.error;
      if (outcome.usage != null) {
        result.usage = outcome.usage;
      }
    }
  } catch (error) {
    result.error = error instanceof Error ? error.message : String(error);
  }
  writeResult(request.result_file, result);
}

const runtimeEntry = process.argv[1];

if (
  runtimeEntry !== undefined &&
  realpathSync(runtimeEntry) === fileURLToPath(import.meta.url)
) {
  main().catch((error) => {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`fatal: ${message}\n`);
    process.exit(1);
  });
}
