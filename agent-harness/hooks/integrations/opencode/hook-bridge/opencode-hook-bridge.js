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
  appendPromptContext,
  appendToolOutputMessage,
  applyUpdatedToolInput,
  blockingDecisionReason,
  hookSpecificOutput,
  preToolUseDenial,
} from "./dispatcher-output.js";

export async function OpenCodeHookBridge({ directory } = {}) {
  const workingDirectory =
    typeof directory === "string" && directory ? directory : process.cwd();
  const sessionsAlreadyStarted = new Set();

  return {
    "chat.message": async (input, output) => {
      if (sessionsAlreadyStarted.has(input.sessionID)) {
        return;
      }
      sessionsAlreadyStarted.add(input.sessionID);
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.sessionStart,
        hookPayload("SessionStart", input.sessionID, workingDirectory, {
          source: "startup",
        }),
      ).catch((failure) => {
        console.error(failure.message);
        return {};
      });
      appendPromptContext(output.parts, additionalContext(dispatcherOutput));
    },
    "tool.execute.before": async (input, output) => {
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.preToolUse,
        toolHookPayload("PreToolUse", input, output.args, workingDirectory),
      );
      const updatedInput = hookSpecificOutput(dispatcherOutput).updatedInput;
      if (isRecord(updatedInput)) {
        applyUpdatedToolInput(output, updatedInput);
      }
      const denial = preToolUseDenial(dispatcherOutput);
      if (denial) {
        throw new Error(denial);
      }
    },
    "tool.execute.after": async (input, output) => {
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.postToolUse,
        toolHookPayload("PostToolUse", input, input.args, workingDirectory),
      );
      const postToolBlock = blockingDecisionReason(dispatcherOutput);
      const turnReviewOutput = await invokeHookDispatcher(
        hookDispatchers.stop,
        hookPayload("Stop", input.sessionID, workingDirectory),
      ).catch((failure) => {
        if (!postToolBlock) {
          throw failure;
        }
        return {};
      });
      if (postToolBlock) {
        throw new Error(postToolBlock);
      }
      const turnReviewBlock = blockingDecisionReason(turnReviewOutput);
      if (turnReviewBlock) {
        throw new Error(turnReviewBlock);
      }
      appendToolOutputMessage(output, dispatcherOutput);
      appendToolOutputMessage(output, turnReviewOutput);
    },
    "experimental.session.compacting": async (input, output) => {
      const dispatcherOutput = await invokeHookDispatcher(
        hookDispatchers.sessionStart,
        hookPayload("SessionStart", input.sessionID, workingDirectory, {
          source: "compact",
        }),
      );
      const context = additionalContext(dispatcherOutput);
      if (context) {
        output.context.push(context);
      }
    },
  };
}
