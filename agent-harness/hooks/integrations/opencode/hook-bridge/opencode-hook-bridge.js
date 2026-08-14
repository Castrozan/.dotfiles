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
  dispatcherFeedback,
  hookSpecificOutput,
  preToolUseDenial,
} from "./dispatcher-output.js";

function textFromParts(parts) {
  if (!Array.isArray(parts)) return "";
  return parts
    .filter((part) => part?.type === "text" && typeof part.text === "string")
    .map((part) => part.text)
    .join("")
    .trim();
}

function finalHumanTurn(messages) {
  let replyText = "";
  let replyMessageID = "";
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index];
    const role = message?.info?.role;
    const text = textFromParts(message?.parts);
    if (!replyText && role === "assistant" && text) {
      replyText = text;
      replyMessageID = message.info.id;
      continue;
    }
    if (replyText && role === "user" && text) {
      return { userRequestText: text, replyText, replyMessageID };
    }
  }
  return { userRequestText: "", replyText, replyMessageID };
}

export async function OpenCodeHookBridge({ directory, client } = {}) {
  const workingDirectory =
    typeof directory === "string" && directory ? directory : process.cwd();
  const sessionsAlreadyStarted = new Set();
  const lastReviewedAssistantMessageBySession = new Map();
  const correctionSourceMessageBySession = new Map();

  return {
    "chat.message": async (input, output) => {
      if (textFromParts(output.parts)) {
        correctionSourceMessageBySession.delete(input.sessionID);
      }
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
      if (postToolBlock) {
        throw new Error(postToolBlock);
      }
      appendToolOutputMessage(output, dispatcherOutput);
    },
    event: async ({ event }) => {
      if (event?.type !== "session.idle") return;
      const sessionID = event?.properties?.sessionID;
      if (!sessionID || !client?.session) return;

      try {
        const response = await client.session.messages({
          path: { id: sessionID },
          query: { directory: workingDirectory },
        });
        const messages = Array.isArray(response?.data) ? response.data : [];
        const { userRequestText, replyText, replyMessageID } =
          finalHumanTurn(messages);
        if (!replyText || !replyMessageID) return;
        if (
          lastReviewedAssistantMessageBySession.get(sessionID) ===
          replyMessageID
        ) {
          return;
        }
        if (
          correctionSourceMessageBySession.has(sessionID) &&
          correctionSourceMessageBySession.get(sessionID) !== replyMessageID
        ) {
          correctionSourceMessageBySession.delete(sessionID);
          lastReviewedAssistantMessageBySession.set(sessionID, replyMessageID);
          return;
        }
        lastReviewedAssistantMessageBySession.set(sessionID, replyMessageID);

        const dispatcherOutput = await invokeHookDispatcher(
          hookDispatchers.stop,
          hookPayload("Stop", sessionID, workingDirectory, {
            user_request_text: userRequestText,
            reply_text: replyText,
          }),
        );
        const feedback = dispatcherFeedback(dispatcherOutput);
        if (!feedback) return;

        correctionSourceMessageBySession.set(sessionID, replyMessageID);
        await client.session.promptAsync({
          path: { id: sessionID },
          query: { directory: workingDirectory },
          body: { system: feedback, parts: [] },
        });
      } catch (failure) {
        correctionSourceMessageBySession.delete(sessionID);
        lastReviewedAssistantMessageBySession.delete(sessionID);
        console.error(failure.message);
      }
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
