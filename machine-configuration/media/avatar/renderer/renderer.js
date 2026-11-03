import * as THREE from "three";
import {
  followLevel,
  RendererControls,
  visibleMode,
} from "./renderer-controls.js";
import { CameraFrameStream } from "./camera-frame-stream.js";
import { CameraLayer } from "./camera-layer.js";
import { CharacterStage } from "./character-stage.js";
import { startFrameClock } from "./frame-clock.js";

const VIDEO_MODES = ["avatar", "camera", "composite"];
const output = document.querySelector("#output");
const status = document.querySelector("#status");
const renderer = new THREE.WebGLRenderer({
  canvas: output,
  antialias: false,
  preserveDrawingBuffer: true,
});
renderer.setSize(1280, 720, false);
renderer.setPixelRatio(1);
renderer.outputEncoding = THREE.sRGBEncoding;
const scene = new THREE.Scene();
scene.background = new THREE.Color("#17202c");
const cameraLayer = new CameraLayer(() => setMode("avatar"));
scene.add(new THREE.AmbientLight(0xffffff, 0.3));
const keyLight = new THREE.DirectionalLight(0xfff4ea, 0.45);
keyLight.position.set(-0.6, 1.6, 2);
scene.add(keyLight);
const camera = new THREE.PerspectiveCamera(30, 1280 / 720, 0.1, 20);
camera.position.set(0, 1.35, 2.0);
camera.lookAt(0, 1.35, 0);
const stage = new CharacterStage(scene, camera);
let lastFrameTime = 0;
const cameraFrames = new URLSearchParams(location.search).has("output")
  ? new CameraFrameStream(
      renderer.getContext(),
      1280,
      720,
      "ws://127.0.0.1:8768",
    )
  : null;
const setPresented = (presented) => {
  output.style.display = presented ? "" : "none";
};
if (cameraFrames) {
  status.hidden = true;
  setPresented(false);
  cameraFrames.connect();
}
const state = {
  mouth: 0,
  mouthTarget: 0,
  mode: "avatar",
  speaking: false,
  lastLevelTime: 0,
  lastVoiceTime: -Infinity,
  idleMode: "breathing",
};

async function loadAvatar() {
  await stage.open();
  status.textContent =
    "Avatar ready · microphone and camera stay under your control";
  window.avatarStatus.ready = true;
}

function drawOutput(timestamp) {
  const mode = visibleMode(state.mode, state.speaking);
  renderer.setViewport(0, 0, 1280, 720);
  if (mode === "camera") cameraLayer.render(renderer, timestamp, state.mouth);
  else renderer.render(scene, camera);
  if (mode === "composite") {
    renderer.autoClear = false;
    renderer.clearDepth();
    renderer.setViewport(880, 24, 384, 216);
    cameraLayer.render(renderer, timestamp, state.mouth);
    renderer.autoClear = true;
  }
}

function render(timestamp) {
  const delta = Math.min((timestamp - lastFrameTime) / 1000, 0.1);
  lastFrameTime = timestamp;
  if (timestamp - state.lastLevelTime > 250) state.mouthTarget = 0;
  state.mouth = followLevel(state.mouth, state.mouthTarget, delta);
  stage.performer?.update(timestamp, delta, state);
  drawOutput(timestamp);
  window.avatarStatus.frames++;
  window.avatarStatus.mouth = state.mouth;
}

function setMode(requested) {
  if (!VIDEO_MODES.includes(requested)) throw new Error("Unknown video mode");
  if (requested !== "avatar" && !cameraLayer.active)
    throw new Error("Enable a camera locally first");
  state.mode = requested;
  window.avatarStatus.mode = state.mode;
}

async function showMode(requested) {
  if (requested === "avatar") {
    disableCamera();
    return;
  }
  if (VIDEO_MODES.includes(requested) && !cameraLayer.active)
    await cameraLayer.enablePreferred();
  setMode(requested);
}

async function enableCamera(deviceId) {
  setMode("avatar");
  await cameraLayer.enable(deviceId);
}

function disableCamera() {
  cameraLayer.disable();
  setMode("avatar");
}

window.avatarStatus = {
  ready: false,
  frames: 0,
  levelMessages: 0,
  mode: state.mode,
  mouth: state.mouth,
};
window.avatar = {
  perform: (action, name) => stage.performer.perform(action, name),
  setExpression: (name, intensity) =>
    stage.performer.setExpression(name, intensity),
  setMode,
  enableCamera,
  disableCamera,
  enableSyntheticCamera: () => {
    cameraLayer.enableSynthetic();
  },
};
window.addEventListener("pagehide", disableCamera);
loadAvatar()
  .then(() =>
    new RendererControls(state, {
      setExpression: ({ expression, intensity }) =>
        stage.performer.setExpression(expression, intensity ?? 1),
      beginSpeech: (message) => stage.performer.beginSpeech(message),
      endSpeech: () => stage.performer.endSpeech(),
      perform: (action, name) => stage.performer.perform(action, name),
      showCharacter: (name) => stage.show(name),
      currentCharacter: () => stage.name,
      showMode,
      setPresented,
      enableCamera,
      disableCamera,
      cameraActive: () => cameraLayer.active,
    }).connect(),
  )
  .catch((error) => {
    status.textContent = error.message;
    window.avatarStatus.error = error.message;
  });
startFrameClock(60, () => {
  render(performance.now());
  cameraFrames?.sendFrame();
});
