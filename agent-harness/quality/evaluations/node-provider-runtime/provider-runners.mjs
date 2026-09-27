import { query } from "@anthropic-ai/claude-agent-sdk";
import { Codex } from "@openai/codex-sdk";
import { startOpenCodeServer } from "./opencode-server.mjs";

import {
  claudeQueryOptions,
  claudeResultOutcome,
  codexInput,
  codexOptions,
  codexThreadOptions,
  normalizeRequestError,
  openCodeConfig,
  openCodeMessageOutcome,
  openCodeSessionInput,
} from "./provider-adapters.mjs";

function timeoutFor(invocation) {
  return (invocation.timeout ?? 120) * 1000;
}

async function runClaude(invocation) {
  const controller = new AbortController();
  const timeoutMs = timeoutFor(invocation);
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let agentQuery;
  try {
    agentQuery = query({
      prompt: invocation.prompt,
      options: {
        ...claudeQueryOptions(invocation),
        abortController: controller,
      },
    });
    for await (const message of agentQuery) {
      if (message.type !== "result") continue;
      return claudeResultOutcome(message);
    }
    return {
      output: null,
      error: "claude query ended without a result message",
    };
  } catch (error) {
    if (controller.signal.aborted) {
      return { output: null, error: `timeout after ${timeoutMs / 1000}s` };
    }
    throw error;
  } finally {
    clearTimeout(timer);
    agentQuery?.close();
  }
}

async function runCodex(invocation) {
  const codex = new Codex(codexOptions(invocation));
  const thread = codex.startThread(codexThreadOptions(invocation));
  const controller = new AbortController();
  const timeoutMs = timeoutFor(invocation);
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const turn = await thread.run(codexInput(invocation), {
      signal: controller.signal,
    });
    return { output: turn.finalResponse, error: null, usage: turn.usage };
  } catch (error) {
    if (controller.signal.aborted) {
      return { output: null, error: `timeout after ${timeoutMs / 1000}s` };
    }
    return { output: null, error: normalizeRequestError(error) };
  } finally {
    clearTimeout(timer);
  }
}

async function runOpenCode(invocation) {
  const controller = new AbortController();
  const timeoutMs = timeoutFor(invocation);
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let server;
  try {
    server = await startOpenCodeServer(
      invocation,
      openCodeConfig(invocation),
      controller.signal,
    );
    const options = { signal: controller.signal };
    const session = await server.client.session.create(
      openCodeSessionInput(invocation),
      options,
    );
    await server.client.session.prompt(
      { sessionID: session.id, text: invocation.prompt },
      options,
    );
    await server.client.session.wait({ sessionID: session.id }, options);
    const messages = await server.client.message.list(
      { sessionID: session.id, order: "desc", type: "assistant", limit: 1 },
      options,
    );
    return openCodeMessageOutcome(messages.data);
  } catch (error) {
    if (controller.signal.aborted) {
      return { output: null, error: `timeout after ${timeoutMs / 1000}s` };
    }
    return { output: null, error: normalizeRequestError(error) };
  } finally {
    clearTimeout(timer);
    await server?.close();
  }
}

const RUNNERS = {
  claude: runClaude,
  codex: runCodex,
  opencode: runOpenCode,
};

export function runnerFor(harness) {
  return RUNNERS[harness];
}
