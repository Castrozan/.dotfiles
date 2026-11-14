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

function stopTracks(stream) {
  for (const track of stream.getTracks()) track.stop();
}

export async function openMicrophone(mediaDevices) {
  const defaultMicrophone = await requestMicrophone(mediaDevices);
  const chosen = chooseMicrophone(await mediaDevices.enumerateDevices());
  if (chosen === null) return defaultMicrophone;
  stopTracks(defaultMicrophone);
  return requestMicrophone(mediaDevices, chosen);
}
