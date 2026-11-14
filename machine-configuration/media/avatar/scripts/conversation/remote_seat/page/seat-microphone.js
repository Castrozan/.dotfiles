const BUILT_IN_LABEL = "(Built-in)";
const VOICE_PROCESSING = {
  channelCount: 1,
  echoCancellation: true,
  noiseSuppression: true,
  autoGainControl: true,
};

function stopStream(stream) {
  for (const track of stream.getTracks()) track.stop();
}

function openedDevice(stream) {
  return stream.getAudioTracks()[0]?.getSettings().deviceId;
}

function isBuiltInInput(device) {
  return (
    device.kind === "audioinput" &&
    device.deviceId !== "default" &&
    device.label.endsWith(BUILT_IN_LABEL)
  );
}

export async function openMicrophone(mediaDevices) {
  const defaultInput = await mediaDevices.getUserMedia({
    audio: VOICE_PROCESSING,
  });
  const builtIn = (await mediaDevices.enumerateDevices()).find(isBuiltInInput);
  if (!builtIn || openedDevice(defaultInput) === builtIn.deviceId)
    return defaultInput;
  stopStream(defaultInput);
  return mediaDevices.getUserMedia({
    audio: { ...VOICE_PROCESSING, deviceId: { exact: builtIn.deviceId } },
  });
}
