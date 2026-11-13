const CALL_MICROPHONE_OUTPUT = "BlackHole 2ch";
const CALL_SPEAKER_INPUT = "BlackHole 16ch";
const CALL_RATE = 16000;
const SYSTEM_DEFAULT_DEVICES = ["default", "communications"];

export function findDevice(devices, kind, name) {
  return devices.find(
    (device) =>
      device.kind === kind &&
      !SYSTEM_DEFAULT_DEVICES.includes(device.deviceId) &&
      device.label.includes(name),
  );
}

export function requireCallDevices(devices) {
  const callMicrophone = findDevice(
    devices,
    "audiooutput",
    CALL_MICROPHONE_OUTPUT,
  );
  const callSpeaker = findDevice(devices, "audioinput", CALL_SPEAKER_INPUT);
  const missing = [
    [CALL_MICROPHONE_OUTPUT, callMicrophone],
    [CALL_SPEAKER_INPUT, callSpeaker],
  ]
    .filter(([, device]) => !device)
    .map(([name]) => name);
  if (missing.length > 0)
    throw new Error(
      `The meeting needs the virtual audio devices ${CALL_MICROPHONE_OUTPUT} and ${CALL_SPEAKER_INPUT}; missing: ${missing.join(", ")}`,
    );
  return { callMicrophone, callSpeaker };
}

function openCallSpeaker(device) {
  return navigator.mediaDevices.getUserMedia({
    audio: {
      deviceId: { exact: device.deviceId },
      echoCancellation: false,
      noiseSuppression: false,
      autoGainControl: false,
    },
  });
}

async function playCallToUser(callAudio) {
  const earpiece = new Audio();
  earpiece.srcObject = callAudio;
  await earpiece.play();
  return earpiece;
}

function openMeetingSocket() {
  const socket = new WebSocket(`ws://${location.host}/meeting`);
  socket.binaryType = "arraybuffer";
  return new Promise((resolve, reject) => {
    socket.onopen = () => resolve(socket);
    socket.onerror = () =>
      reject(new Error("The meeting socket did not open on the avatar"));
  });
}

function sendCallFrames(capture, callAudio, socket) {
  const frames = new AudioWorkletNode(capture, "microphone-frames", {
    channelCount: 1,
    channelCountMode: "explicit",
  });
  capture.createMediaStreamSource(callAudio).connect(frames);
  frames.port.onmessage = (event) => {
    if (socket.readyState === WebSocket.OPEN) socket.send(event.data);
  };
}

async function openCallMicrophone(output, microphone, voiceForCall) {
  const context = new AudioContext();
  await context.setSinkId(output.deviceId);
  for (const stream of [microphone, voiceForCall.stream])
    context.createMediaStreamSource(stream).connect(context.destination);
  await context.resume();
  return context;
}

export async function joinMeeting({
  microphone,
  playback,
  voice,
  openAudioGraph,
}) {
  const { callMicrophone, callSpeaker } = requireCallDevices(
    await navigator.mediaDevices.enumerateDevices(),
  );
  const callAudio = await openCallSpeaker(callSpeaker);
  const earpiece = await playCallToUser(callAudio);
  const capture = await openAudioGraph(CALL_RATE);
  const socket = await openMeetingSocket();
  sendCallFrames(capture, callAudio, socket);
  const voiceForCall = playback.createMediaStreamDestination();
  voice.connect(voiceForCall);
  const toCall = await openCallMicrophone(
    callMicrophone,
    microphone,
    voiceForCall,
  );
  return {
    closed: new Promise((resolve) => {
      socket.onclose = resolve;
    }),
    leave() {
      for (const track of callAudio.getTracks()) track.stop();
      earpiece.srcObject = null;
      socket.onclose = null;
      socket.close();
      for (const graph of [capture, toCall])
        if (graph.state !== "closed") graph.close();
    },
  };
}
