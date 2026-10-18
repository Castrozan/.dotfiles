import { spawn } from "node:child_process";

const hookDispatcherPath = "@piHookDispatcher@";
const sessionStartDispatcherPath = "@piSessionStartDispatcher@";
const hookTimeoutMilliseconds = 15000;

function messageText(message) {
  if (typeof message?.content === "string") return message.content.trim();
  if (!Array.isArray(message?.content)) return "";
  return message.content
    .filter((part) => part?.type === "text" && typeof part.text === "string")
    .map((part) => part.text)
    .join("")
    .trim();
}

function parseHookOutput(stdout, stderr, exitCode) {
  if (exitCode !== 0) {
    throw new Error(stderr.trim() || `Pi reply guard exited ${exitCode}`);
  }
  try {
    return stdout.trim() ? JSON.parse(stdout) : {};
  } catch {
    throw new Error("Pi reply guard returned invalid JSON");
  }
}

function invokeReplyGuard(payload) {
  return new Promise((resolve, reject) => {
    const dispatcher =
      payload.hook_event_name === "SessionStart"
        ? sessionStartDispatcherPath
        : hookDispatcherPath;
    const child = spawn(dispatcher, [], {
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    const timeout = setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error("Pi reply guard exceeded 15000ms"));
    }, hookTimeoutMilliseconds);
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => (stdout += chunk));
    child.stderr.on("data", (chunk) => (stderr += chunk));
    child.on("error", reject);
    child.on("close", (exitCode) => {
      clearTimeout(timeout);
      try {
        resolve(parseHookOutput(stdout, stderr, exitCode));
      } catch (failure) {
        reject(failure);
      }
    });
    child.stdin.end(JSON.stringify(payload));
  });
}

async function checkSettledReply(
  pi,
  correctedReply,
  userRequestText,
  replyText,
  setCorrectionPending,
) {
  const output = await invokeReplyGuard({
    hook_event_name: "Stop",
    session_id: "pi-interactive-session",
    user_request_text: userRequestText,
    reply_text: replyText,
    ...(correctedReply ? { stop_hook_active: true } : {}),
  });
  if (correctedReply) return;
  const feedback = output.reason || output.systemMessage;
  if (!feedback) return;
  setCorrectionPending();
  pi.sendMessage(
    {
      customType: "human-facing-reply-format-guard",
      content: feedback,
      display: false,
    },
    { triggerTurn: true, deliverAs: "followUp" },
  );
}

async function readSessionContext() {
  const output = await invokeReplyGuard({ hook_event_name: "SessionStart" });
  if (output.continue === false) throw new Error(output.stopReason);
  return output.hookSpecificOutput?.additionalContext || "";
}

function createSessionStartHandler() {
  let sessionContext;
  return async (event) => {
    if (sessionContext === undefined) {
      sessionContext = await readSessionContext();
    }
    if (sessionContext) {
      return { systemPrompt: `${event.systemPrompt}\n\n${sessionContext}` };
    }
  };
}

function updateReplyState(state, event) {
  const text = messageText(event.message);
  if (event.message.role === "user" && text) {
    state.userRequestText = text;
    state.replyText = "";
    state.correctionPending = false;
  } else if (event.message.role === "assistant" && text) {
    state.replyText = text;
  }
}

async function checkSessionReply(pi, state) {
  const correctedReply = state.correctionPending;
  state.correctionPending = false;
  if (!state.replyText) return;
  try {
    await checkSettledReply(
      pi,
      correctedReply,
      state.userRequestText,
      state.replyText,
      () => {
        state.correctionPending = true;
      },
    );
  } catch (failure) {
    console.error(failure.message);
  }
}

export default function HumanFacingReplyGuard(pi) {
  const state = {
    userRequestText: "",
    replyText: "",
    correctionPending: false,
  };
  pi.on("before_agent_start", createSessionStartHandler());
  pi.on("message_end", (event) => updateReplyState(state, event));
  pi.on("agent_settled", () => checkSessionReply(pi, state));
}
