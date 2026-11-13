import { chooseMicrophone } from "/microphone-choice.js";

const MICROPHONE_RATE = 16000;
const WORKLETS = "/seat-audio-worklets.js";
const state = document.getElementById("state");

function requestMicrophone(deviceId) {
  return navigator.mediaDevices.getUserMedia({
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

async function openMicrophone() {
  const defaultMicrophone = await requestMicrophone();
  const chosen = chooseMicrophone(
    await navigator.mediaDevices.enumerateDevices(),
  );
  if (chosen === null) return defaultMicrophone;
  stopTracks(defaultMicrophone);
  return requestMicrophone(chosen);
}

async function openAudioGraph() {
  const context = new AudioContext({ sampleRate: MICROPHONE_RATE });
  await context.audioWorklet.addModule(WORKLETS);
  await context.resume();
  return context;
}

async function captureForTheWake() {
  const microphone = await openMicrophone();
  const capture = await openAudioGraph();
  const frames = new AudioWorkletNode(capture, "microphone-frames");
  const socket = new WebSocket(`ws://${location.host}/audio`);
  socket.binaryType = "arraybuffer";
  capture.createMediaStreamSource(microphone).connect(frames);
  frames.port.onmessage = (event) => {
    if (socket.readyState === WebSocket.OPEN) socket.send(event.data);
  };
  socket.onopen = () => {
    state.textContent = "The wake listener hears through this page";
  };
  socket.onclose = () => {
    stopTracks(microphone);
    capture.close();
    window.close();
  };
}

captureForTheWake().catch((error) => {
  const failure = `${error.name}: ${error.message}`;
  state.textContent = failure;
  fetch(`/failure?${encodeURIComponent(failure)}`);
});
