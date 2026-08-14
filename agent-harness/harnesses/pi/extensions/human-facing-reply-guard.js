import { spawn } from "node:child_process";

const hookDispatcherPath = "@piHookDispatcher@";
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

function invokeReplyGuard(payload) {
  return new Promise((resolve, reject) => {
    const child = spawn(hookDispatcherPath, [], {
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
      if (exitCode !== 0) {
        reject(new Error(stderr.trim() || `Pi reply guard exited ${exitCode}`));
        return;
      }
      try {
        resolve(stdout.trim() ? JSON.parse(stdout) : {});
      } catch {
        reject(new Error("Pi reply guard returned invalid JSON"));
      }
    });
    child.stdin.end(JSON.stringify(payload));
  });
}

export default function HumanFacingReplyGuard(pi) {
  let userRequestText = "";
  let replyText = "";
  let correctionPending = false;

  pi.on("message_end", (event) => {
    const text = messageText(event.message);
    if (event.message.role === "user" && text) {
      userRequestText = text;
      replyText = "";
      correctionPending = false;
    } else if (event.message.role === "assistant" && text) {
      replyText = text;
    }
  });

  pi.on("agent_settled", async () => {
    if (correctionPending) {
      correctionPending = false;
      return;
    }
    if (!replyText) return;

    try {
      const output = await invokeReplyGuard({
        hook_event_name: "Stop",
        session_id: "pi-interactive-session",
        user_request_text: userRequestText,
        reply_text: replyText,
      });
      const feedback = output.reason || output.systemMessage;
      if (!feedback) return;
      correctionPending = true;
      pi.sendMessage(
        {
          customType: "human-facing-reply-format-guard",
          content: feedback,
          display: false,
        },
        { triggerTurn: true, deliverAs: "followUp" },
      );
    } catch (failure) {
      console.error(failure.message);
    }
  });
}
