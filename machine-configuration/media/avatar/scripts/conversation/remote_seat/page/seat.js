import { joinMeeting } from "/meeting-seat.js";

const MICROPHONE_RATE = 16000;
const VOICE_RATE = 24000;
const WORKLETS = "/seat-audio-worklets.js";
const state = document.getElementById("state");
const noMeeting = {
  closed: new Promise(() => {}),
  setLevels() {},
  leave() {},
};

function openMicrophone() {
  return navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });
}

async function openAudioGraph(sampleRate) {
  const context = new AudioContext({ sampleRate });
  await context.audioWorklet.addModule(WORKLETS);
  await context.resume();
  return context;
}

function leaveSeat(microphone, graphs, meeting) {
  for (const track of microphone.getTracks()) track.stop();
  for (const graph of graphs) if (graph.state !== "closed") graph.close();
  meeting.leave();
  window.close();
}

async function takeSeat() {
  const microphone = await openMicrophone();
  const capture = await openAudioGraph(MICROPHONE_RATE);
  const playback = await openAudioGraph(VOICE_RATE);
  const frames = new AudioWorkletNode(capture, "microphone-frames");
  const voice = new AudioWorkletNode(playback, "voice-playback");
  const meeting = new URLSearchParams(location.search).has("meeting")
    ? await joinMeeting({ microphone, playback, voice, openAudioGraph })
    : noMeeting;
  const leave = () => leaveSeat(microphone, [capture, playback], meeting);
  const socket = new WebSocket(`ws://${location.host}/audio`);
  socket.binaryType = "arraybuffer";
  capture.createMediaStreamSource(microphone).connect(frames);
  voice.connect(playback.destination);
  frames.port.onmessage = (event) => {
    if (socket.readyState === WebSocket.OPEN) socket.send(event.data);
  };
  socket.onmessage = (event) => {
    if (typeof event.data === "string")
      meeting.setLevels(JSON.parse(event.data));
    else voice.port.postMessage(event.data, [event.data]);
  };
  socket.onopen = () => {
    state.textContent = "The avatar hears and speaks through this machine";
  };
  socket.onclose = leave;
  meeting.closed.then(leave);
}

takeSeat().catch((error) => {
  const failure = `${error.name}: ${error.message}`;
  state.textContent = failure;
  fetch(`/failure?${encodeURIComponent(failure)}`);
});
