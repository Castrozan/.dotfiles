import { isRecord, opencodeToolInput } from "./payload-translation.js";

export function hookSpecificOutput(dispatcherOutput) {
  return isRecord(dispatcherOutput.hookSpecificOutput)
    ? dispatcherOutput.hookSpecificOutput
    : {};
}

export function additionalContext(dispatcherOutput) {
  const context = hookSpecificOutput(dispatcherOutput).additionalContext;
  return typeof context === "string" && context ? context : "";
}

function dispatcherMessages(dispatcherOutput) {
  const messages = [
    dispatcherOutput.systemMessage,
    dispatcherOutput.reason,
    additionalContext(dispatcherOutput),
  ].filter((message) => typeof message === "string" && message);
  return [...new Set(messages)];
}

export function appendToolOutputMessage(toolOutput, dispatcherOutput) {
  const messages = dispatcherMessages(dispatcherOutput);
  if (messages.length === 0) {
    return;
  }
  const existingOutput =
    typeof toolOutput.output === "string" ? toolOutput.output : "";
  toolOutput.output = [existingOutput, ...messages]
    .filter(Boolean)
    .join("\n\n");
}

export function appendPromptContext(parts, context) {
  if (!context || !Array.isArray(parts)) {
    return;
  }
  const textPart = parts.find(
    (part) =>
      isRecord(part) && part.type === "text" && typeof part.text === "string",
  );
  if (!textPart) {
    return;
  }
  textPart.text = [textPart.text, context].filter(Boolean).join("\n\n");
}

export function applyUpdatedToolInput(toolOutput, updatedInput) {
  const translatedInput = opencodeToolInput(updatedInput);
  if (!isRecord(toolOutput.args)) {
    toolOutput.args = translatedInput;
    return;
  }
  for (const key of Object.keys(toolOutput.args)) {
    delete toolOutput.args[key];
  }
  Object.assign(toolOutput.args, translatedInput);
}

export function preToolUseDenial(dispatcherOutput) {
  const specificOutput = hookSpecificOutput(dispatcherOutput);
  if (!new Set(["block", "deny"]).has(specificOutput.permissionDecision)) {
    return "";
  }
  return (
    specificOutput.permissionDecisionReason ||
    dispatcherOutput.reason ||
    dispatcherOutput.systemMessage ||
    "OpenCode blocked this tool call."
  );
}

export function blockingDecisionReason(dispatcherOutput) {
  if (!new Set(["block", "deny"]).has(dispatcherOutput.decision)) {
    return "";
  }
  return (
    dispatcherOutput.reason ||
    dispatcherOutput.systemMessage ||
    "OpenCode blocked this tool result."
  );
}
