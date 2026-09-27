const canonicalToolNames = {
  shell: "Bash",
  edit: "Edit",
  skill: "Skill",
  subagent: "Agent",
  patch: "apply_patch",
  webfetch: "WebFetch",
  write: "Write",
};

const opencodeArgumentNames = {
  file_path: "path",
  new_string: "newString",
  old_string: "oldString",
  patch_text: "patchText",
  subagent_type: "agent",
  skill: "id",
};

export function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function snakeCaseKey(key) {
  if (key === "path") return "file_path";
  return key.replace(/[A-Z]/g, (character) => `_${character.toLowerCase()}`);
}

function normalizeToolInput(value) {
  if (Array.isArray(value)) {
    return value.map(normalizeToolInput);
  }
  if (!isRecord(value)) {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value).map(([key, child]) => [
      snakeCaseKey(key),
      normalizeToolInput(child),
    ]),
  );
}

export function opencodeToolInput(value) {
  if (Array.isArray(value)) {
    return value.map(opencodeToolInput);
  }
  if (!isRecord(value)) {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value).map(([key, child]) => [
      opencodeArgumentNames[key] ?? key,
      opencodeToolInput(child),
    ]),
  );
}

export function canonicalToolName(toolName) {
  return canonicalToolNames[toolName] ?? toolName;
}

function toolInputForDispatcher(toolName, toolInput) {
  const normalizedInput = normalizeToolInput(toolInput);
  if (
    canonicalToolName(toolName) === "apply_patch" &&
    isRecord(normalizedInput) &&
    typeof normalizedInput.patch_text === "string"
  ) {
    return normalizedInput.patch_text;
  }
  if (canonicalToolName(toolName) === "Agent" && isRecord(normalizedInput)) {
    const { agent, ...remainingInput } = normalizedInput;
    return { ...remainingInput, subagent_type: agent };
  }
  if (
    canonicalToolName(toolName) !== "Skill" ||
    !isRecord(normalizedInput) ||
    typeof normalizedInput.id !== "string"
  ) {
    return normalizedInput;
  }
  const { id, ...remainingInput } = normalizedInput;
  return { ...remainingInput, skill: id };
}

export function hookPayload(
  eventName,
  sessionID,
  directory,
  additionalFields = {},
) {
  return {
    hook_event_name: eventName,
    session_id: sessionID ?? "",
    cwd: directory,
    ...additionalFields,
  };
}

export function toolHookPayload(eventName, input, args, directory) {
  return hookPayload(eventName, input.sessionID, directory, {
    tool_name: canonicalToolName(input.tool),
    tool_input: toolInputForDispatcher(input.tool, args),
  });
}
