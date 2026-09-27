import {
  hookDispatchers,
  invokeHookDispatcher,
} from "./dispatcher-invocation.js";
import { dispatcherFeedback } from "./dispatcher-output.js";
import { hookPayload } from "./payload-translation.js";

export function createReplyGuard(context, workingDirectory) {
  const sessions = new Map();

  async function review(sessionID, state) {
    if (!state.replyText || state.reviewedMessageID === state.replyMessageID)
      return;
    const correctedReply = Boolean(
      state.correctionMessageID &&
        state.correctionMessageID !== state.replyMessageID,
    );
    state.reviewedMessageID = state.replyMessageID;
    const dispatcherOutput = await invokeHookDispatcher(
      hookDispatchers.stop,
      hookPayload("Stop", sessionID, workingDirectory, {
        user_request_text: state.userRequestText,
        reply_text: state.replyText,
        ...(correctedReply ? { stop_hook_active: true } : {}),
      }),
    );
    if (correctedReply) return;
    const feedback = dispatcherFeedback(dispatcherOutput);
    if (!feedback) return;
    state.correctionMessageID = state.replyMessageID;
    await context.session.synthetic({
      sessionID,
      text: feedback,
      delivery: "queue",
      resume: true,
    });
  }

  return {
    startTurn(sessionID, userRequestText) {
      sessions.set(sessionID, { userRequestText, replyText: "" });
    },
    async handleEvent(event) {
      const sessionID = event.data?.sessionID;
      const state = sessions.get(sessionID);
      if (!state) return;
      if (event.type === "session.deleted") {
        sessions.delete(sessionID);
        return;
      }
      if (event.type === "session.step.started") {
        state.replyMessageID = event.data.assistantMessageID;
        state.replyText = "";
      }
      if (event.type === "session.text.ended") {
        if (state.replyMessageID !== event.data.assistantMessageID) {
          state.replyMessageID = event.data.assistantMessageID;
          state.replyText = "";
        }
        state.replyText += event.data.text;
      }
      if (event.type !== "session.execution.succeeded") return;
      try {
        await review(sessionID, state);
      } catch (failure) {
        state.reviewedMessageID = undefined;
        state.correctionMessageID = undefined;
        console.error(failure.message);
      }
    },
    clear() {
      sessions.clear();
    },
  };
}
