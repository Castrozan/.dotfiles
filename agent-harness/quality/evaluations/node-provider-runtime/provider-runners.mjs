import { query } from "@anthropic-ai/claude-agent-sdk";
import { Codex } from "@openai/codex-sdk";
import { createOpencode } from "@opencode-ai/sdk";
import { createServer } from "node:net";

import {
  claudeQueryOptions,
  claudeResultOutcome,
  codexInput,
  codexOptions,
  codexThreadOptions,
  collectOpenCodeTextParts,
  normalizeRequestError,
  openCodeConfig,
  openCodePromptBody,
  openCodeToolSelection,
} from "./provider-adapters.mjs";

function timeoutFor(invocation) {
  return (invocation.timeout ?? 120) * 1000;
}

function availableLoopbackPort() {
  return new Promise((resolve, reject) => {
    const socketServer = createServer();
    socketServer.unref();
    socketServer.once("error", reject);
    socketServer.listen(0, "127.0.0.1", () => {
      const address = socketServer.address();
      socketServer.close((error) => {
        if (error) reject(error);
        else resolve(address.port);
      });
    });
  });
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
  const codex = new Codex(codexOptions());
  const thread = codex.startThread(codexThreadOptions(invocation));
  const controller = new AbortController();
  const timeoutMs = timeoutFor(invocation);
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const turn = await thread.run(codexInput(invocation), {
      signal: controller.signal,
    });
    return { output: turn.finalResponse, error: null };
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
    const port = await availableLoopbackPort();
    const opencode = await createOpencode({
      config: openCodeConfig(invocation),
      port,
      signal: controller.signal,
      timeout: timeoutMs,
    });
    server = opencode.server;
    const toolIdentifiers = await opencode.client.tool.ids({
      query: { directory: invocation.working_directory },
      signal: controller.signal,
    });
    if (toolIdentifiers.error) {
      return {
        output: null,
        error: normalizeRequestError(toolIdentifiers.error),
      };
    }
    const tools = openCodeToolSelection(
      toolIdentifiers.data,
      invocation.no_tools,
    );
    const session = await opencode.client.session.create({
      query: { directory: invocation.working_directory },
      signal: controller.signal,
    });
    if (session.error) {
      return { output: null, error: normalizeRequestError(session.error) };
    }
    const message = await opencode.client.session.prompt({
      path: { id: session.data.id },
      query: { directory: invocation.working_directory },
      body: openCodePromptBody(invocation, tools),
      signal: controller.signal,
    });
    if (message.error) {
      return { output: null, error: normalizeRequestError(message.error) };
    }
    return {
      output: collectOpenCodeTextParts(message.data.parts),
      error: null,
    };
  } catch (error) {
    if (controller.signal.aborted) {
      return { output: null, error: `timeout after ${timeoutMs / 1000}s` };
    }
    return { output: null, error: normalizeRequestError(error) };
  } finally {
    clearTimeout(timer);
    server?.close();
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
