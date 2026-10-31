import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RendererControls } from "./renderer-controls.js";
import { CameraLayer } from "./camera-layer.js";
import { VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";

const output = document.querySelector("#output");
const status = document.querySelector("#status");
const renderer = new THREE.WebGLRenderer({ canvas: output, antialias: false });
renderer.setSize(1280, 720, false);
renderer.setPixelRatio(1);
renderer.outputEncoding = THREE.sRGBEncoding;
const scene = new THREE.Scene();
scene.background = new THREE.Color("#17202c");
const cameraLayer = new CameraLayer(() => setMode("avatar"));
scene.add(new THREE.HemisphereLight(0xffffff, 0x58617b, 2));
const camera = new THREE.PerspectiveCamera(30, 1280 / 720, 0.1, 20);
camera.position.set(0, 1.35, 2.0);
camera.lookAt(0, 1.35, 0);
const loader = new GLTFLoader();
loader.register((parser) => new VRMLoaderPlugin(parser));
let avatar;
let lastFrameTime = 0;
const state = {
  mouth: 0,
  mode: "avatar",
  lastLevelTime: 0,
  expression: "neutral",
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
  camera.position.set(0, headPosition.y - 0.12, 1.8);
  camera.lookAt(0, headPosition.y - 0.12, 0);
  for (const [bone, angle] of [
    ["leftUpperArm", 1.15],
    ["rightUpperArm", -1.15],
  ]) {
    const node = avatar.humanoid.getNormalizedBoneNode(bone);
    if (node) node.rotation.z = angle;
  }
  status.textContent =
    "Avatar ready · microphone and camera stay under your control";
  if (new URLSearchParams(location.search).has("output")) status.hidden = true;
  window.avatarStatus.ready = true;
}

function idleHeight(timestamp) {
  if (state.idleMode === "floating") return Math.sin(timestamp / 1500) * 0.03;
  if (state.idleMode === "breathing") return Math.sin(timestamp / 500) * 0.003;
  return 0;
}

function updateAvatar(timestamp, delta) {
  if (!avatar) return;
  avatar.expressionManager.setValue("aa", state.mouth);
  avatar.expressionManager.setValue(
    "blink",
    Math.sin((timestamp / 1000) * 1.1) > 0.995 ? 1 : 0,
  );
  avatar.scene.position.y = idleHeight(timestamp);
  avatar.update(delta);
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
  if (timestamp - state.lastLevelTime > 250) state.mouth = 0;
  updateAvatar(timestamp, delta);
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

function setExpression(message) {
  avatar?.expressionManager.setValue(state.expression, 0);
  state.expression = message.expression;
  avatar?.expressionManager.setValue(state.expression, message.intensity ?? 1);
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
      setExpression,
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
