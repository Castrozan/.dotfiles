const canonicalToolNames = {
  bash: "Bash",
  edit: "Edit",
  skill: "Skill",
  task: "Agent",
  webfetch: "WebFetch",
  write: "Write",
};

const opencodeArgumentNames = {
  file_path: "filePath",
  new_string: "newString",
  old_string: "oldString",
  patch_text: "patchText",
};

export function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function snakeCaseKey(key) {
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
  if (
    canonicalToolName(toolName) !== "Skill" ||
    !isRecord(normalizedInput) ||
    typeof normalizedInput.name !== "string"
  ) {
    return normalizedInput;
  }
  const { name, ...remainingInput } = normalizedInput;
  return { ...remainingInput, skill: name };
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
