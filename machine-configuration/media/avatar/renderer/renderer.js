import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { followLevel, RendererControls } from "./renderer-controls.js";
import { CameraLayer } from "./camera-layer.js";
import { AvatarPerformer } from "./avatar-performer.js";
import { faceMorphNames } from "./face-expressions.js";
import { VRMExpression, VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";

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
const loader = new GLTFLoader();
loader.register((parser) => new VRMLoaderPlugin(parser));
let avatar;
let performer;
let lastFrameTime = 0;
if (new URLSearchParams(location.search).has("output")) {
  status.hidden = true;
  output.style.display = "none";
}
const state = {
  mouth: 0,
  mouthTarget: 0,
  mode: "avatar",
  lastLevelTime: 0,
  lastVoiceTime: -Infinity,
  idleMode: "breathing",
};

async function loadAvatar() {
  const gltf = await loader.loadAsync("/model.vrm");
  avatar = gltf.userData.vrm;
  VRMUtils.rotateVRM0(avatar);
  scene.add(avatar.scene);
  avatar.scene.updateMatrixWorld(true);
  const head = avatar.humanoid.getNormalizedBoneNode("head");
  const headPosition = new THREE.Vector3();
  head.getWorldPosition(headPosition);
  camera.position.set(0, headPosition.y - 0.04, 1);
  camera.lookAt(0, headPosition.y - 0.04, 0);
  const gazeTarget = new THREE.Object3D();
  scene.add(gazeTarget);
  performer = new AvatarPerformer({
    vrm: avatar,
    morphNames: faceMorphNames(gltf.parser.json),
    gazeTarget,
    gazeOrigin: camera.position.clone(),
    createExpression: (name) => new VRMExpression(name),
  });
  status.textContent =
    "Avatar ready · microphone and camera stay under your control";
  window.avatarStatus.ready = true;
}

function drawOutput(timestamp) {
  renderer.setViewport(0, 0, 1280, 720);
  if (state.mode === "camera")
    cameraLayer.render(renderer, timestamp, state.mouth);
  else renderer.render(scene, camera);
  if (state.mode === "composite") {
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
  performer?.update(timestamp, delta, state);
  drawOutput(timestamp);
  window.avatarStatus.frames++;
  window.avatarStatus.mouth = state.mouth;
}

function setMode(requested) {
  if (!["avatar", "camera", "composite"].includes(requested))
    throw new Error("Unknown video mode");
  if (requested !== "avatar" && !cameraLayer.active)
    throw new Error("Enable a camera locally first");
  state.mode = requested;
  window.avatarStatus.mode = state.mode;
}

async function enableCamera(deviceId) {
  setMode("avatar");
  await cameraLayer.enable(deviceId);
}

function disableCamera() {
  cameraLayer.disable();
  setMode("avatar");
}

window.avatarFrameJpeg = (quality) =>
  output.toDataURL("image/jpeg", quality).split(",")[1];

window.avatarStatus = {
  ready: false,
  frames: 0,
  levelMessages: 0,
  mode: state.mode,
  mouth: state.mouth,
};
window.avatar = {
  perform: (action, name) => performer.perform(action, name),
  setExpression: (name, intensity) => performer.setExpression(name, intensity),
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
        performer.setExpression(expression, intensity ?? 1),
      beginSpeech: (message) => performer.beginSpeech(message),
      endSpeech: () => performer.endSpeech(),
      perform: (action, name) => performer.perform(action, name),
      setMode,
      enableCamera,
      disableCamera,
      cameraActive: () => cameraLayer.active,
    }).connect(),
  )
  .catch((error) => {
    status.textContent = error.message;
    window.avatarStatus.error = error.message;
  });
setInterval(() => render(performance.now()), 1000 / 15);
