import { chooseMicrophone } from "/microphone-choice.js";

function requestMicrophone(mediaDevices, deviceId) {
  return mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      ...(deviceId && { deviceId: { exact: deviceId } }),
    },
  });
}

export async function openMicrophone(mediaDevices) {
  const chosen = chooseMicrophone(await mediaDevices.enumerateDevices());
  return requestMicrophone(mediaDevices, chosen);
}
