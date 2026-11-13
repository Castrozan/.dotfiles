const VIRTUAL_DEFAULTS = new Set(["default", "communications"]);

function isInput(device) {
  return device.kind === "audioinput";
}

function labelled(device, word) {
  return device.label.toLowerCase().includes(word);
}

function isBuiltIn(device) {
  return !VIRTUAL_DEFAULTS.has(device.deviceId) && labelled(device, "built-in");
}

function currentInput(inputs) {
  return inputs.find((device) => device.deviceId === "default") ?? inputs[0];
}

function isBluetooth(device) {
  return device !== undefined && labelled(device, "bluetooth");
}

function builtInId(inputs) {
  return inputs.find(isBuiltIn)?.deviceId ?? null;
}

export function chooseMicrophone(devices) {
  const inputs = devices.filter(isInput);
  if (!isBluetooth(currentInput(inputs))) return null;
  return builtInId(inputs);
}
