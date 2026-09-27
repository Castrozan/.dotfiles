import {
  hookDispatchers,
  invokeHookDispatcher,
} from "./dispatcher-invocation.js";
import {
  hookPayload,
  isRecord,
  toolHookPayload,
} from "./payload-translation.js";
import {
  additionalContext,
  appendToolOutputMessage,
  applyUpdatedToolInput,
  blockingDecisionReason,
  hookSpecificOutput,
  preToolUseDenial,
} from "./dispatcher-output.js";
import { createReplyGuard } from "./reply-guard.js";

export default {
  id: "dotfiles.hook-bridge",
  async setup(context) {
    const workingDirectory = context.location.directory;
    const sessionsAlreadyStarted = new Set();
    const replyGuard = createReplyGuard(context, workingDirectory);
    const controller = new AbortController();

    await context.session.hook("prompt", async (event) => {
      replyGuard.startTurn(event.sessionID, event.prompt.text);
      if (sessionsAlreadyStarted.has(event.sessionID)) return;
      sessionsAlreadyStarted.add(event.sessionID);
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.sessionStart,
        hookPayload("SessionStart", event.sessionID, workingDirectory, {
          source: "startup",
        }),
      ).catch((error_) => {
        sessionsAlreadyStarted.delete(event.sessionID);
        console.error(error_.message);
        return {};
      });
      const additional = additionalContext(dispatcherOutput);
      if (additional) event.prompt.text += `\n\n${additional}`;
    });

    await context.tool.hook("execute.before", async (event) => {
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.preToolUse,
        toolHookPayload("PreToolUse", event, event.input, workingDirectory),
      );
      const updatedInput = hookSpecificOutput(dispatcherOutput).updatedInput;
      if (isRecord(updatedInput)) applyUpdatedToolInput(event, updatedInput);
      const denial = preToolUseDenial(dispatcherOutput);
      if (denial) throw new Error(denial);
    });

    await context.tool.hook("execute.after", async (event) => {
      if (event.status !== "completed") return;
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.postToolUse,
        toolHookPayload("PostToolUse", event, event.input, workingDirectory),
      );
      const denial = blockingDecisionReason(dispatcherOutput);
      if (denial) throw new Error(denial);
      appendToolOutputMessage(event.result, dispatcherOutput);
    });

    await context.session.hook("compaction", async (event) => {
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.sessionStart,
        hookPayload("SessionStart", event.sessionID, workingDirectory, {
          source: "compact",
        }),
      );
      const additional = additionalContext(dispatcherOutput);
      if (additional) event.system.push({ type: "text", text: additional });
    });

    const events = (async () => {
      for await (const event of context.event.subscribe({
        signal: controller.signal,
      })) {
        if (event.type === "session.deleted") {
          sessionsAlreadyStarted.delete(event.data.sessionID);
        }
        await replyGuard.handleEvent(event);
      }
    })().catch((error_) => {
      if (!controller.signal.aborted) console.error(error_.message);
    });

    return async () => {
      controller.abort();
      await events;
      sessionsAlreadyStarted.clear();
      replyGuard.clear();
    };
  },
};
