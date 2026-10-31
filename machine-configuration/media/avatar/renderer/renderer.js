import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
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
const cameraLayer = new CameraLayer();
const localControls = new BroadcastChannel("avatar-local-controls");
scene.add(new THREE.HemisphereLight(0xffffff, 0x58617b, 2));
const camera = new THREE.PerspectiveCamera(30, 1280 / 720, 0.1, 20);
camera.position.set(0, 1.35, 2.0);
camera.lookAt(0, 1.35, 0);
const loader = new GLTFLoader();
loader.register((parser) => new VRMLoaderPlugin(parser));
let avatar;
let mouth = 0;
let mode = "avatar";
let socket;
let lastLevelTime = 0;
let lastFrameTime = 0;
let expression = "neutral";

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

function render(timestamp) {
  const delta = Math.min((timestamp - lastFrameTime) / 1000, 0.1);
  lastFrameTime = timestamp;
  if (timestamp - lastLevelTime > 250) mouth = 0;
  if (avatar) {
    avatar.expressionManager.setValue("aa", mouth);
    avatar.expressionManager.setValue(
      "blink",
      Math.sin((timestamp / 1000) * 1.1) > 0.995 ? 1 : 0,
    );
    avatar.update(delta);
  }
  renderer.setViewport(0, 0, 1280, 720);
  if (mode === "camera") cameraLayer.render(renderer, timestamp, mouth);
  else renderer.render(scene, camera);
  if (mode === "composite") {
    renderer.autoClear = false;
    renderer.clearDepth();
    renderer.setViewport(880, 24, 384, 216);
    cameraLayer.render(renderer, timestamp, mouth);
    renderer.autoClear = true;
  }
  window.avatarStatus.frames++;
  window.avatarStatus.mouth = mouth;
}

function setMode(requested) {
  if (!["avatar", "camera", "composite"].includes(requested))
    throw new Error("Unknown video mode");
  if (requested !== "avatar" && !cameraLayer.active)
    throw new Error("Enable a camera locally first");
  mode = requested;
  window.avatarStatus.mode = mode;
}

function handleMessage(message) {
  if (message.type === "audioLevel") {
    mouth = Math.max(0, Math.min(1, message.level * 5));
    lastLevelTime = performance.now();
    window.avatarStatus.levelMessages++;
  } else if (message.type === "updateExpression") {
    avatar?.expressionManager.setValue(expression, 0);
    expression = message.expression;
    avatar?.expressionManager.setValue(expression, message.intensity ?? 1);
  } else if (message.type === "setVideoMode") {
    try {
      setMode(message.mode);
      socket.send(
        JSON.stringify({ type: "videoModeChanged", mode, id: message.id }),
      );
    } catch (error) {
      socket.send(
        JSON.stringify({
          type: "videoModeError",
          message: error.message,
          id: message.id,
        }),
      );
    }
  }
}

function connect() {
  socket = new WebSocket("ws://127.0.0.1:8765");
  socket.onopen = () =>
    socket.send(JSON.stringify({ type: "identify", role: "renderer" }));
  socket.onmessage = (event) => handleMessage(JSON.parse(event.data));
  socket.onclose = () => {
    mouth = 0;
    setTimeout(connect, 1500);
  };
}

async function enableCamera(deviceId) {
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
  mode,
  mouth,
};
window.avatar = {
  setMode,
  enableCamera,
  disableCamera,
  enableSyntheticCamera: () => {
    cameraLayer.enableSynthetic();
  },
};
localControls.onmessage = async (event) => {
  try {
    if (event.data.type === "enableCamera")
      await enableCamera(event.data.deviceId);
    if (event.data.type === "disableCamera") disableCamera();
    localControls.postMessage({
      type: "cameraResult",
      message: cameraLayer.active ? "Camera enabled" : "Camera released",
    });
  } catch (error) {
    localControls.postMessage({ type: "cameraResult", message: error.message });
  }
};
window.addEventListener("pagehide", disableCamera);
loadAvatar()
  .then(connect)
  .catch((error) => {
    status.textContent = error.message;
    window.avatarStatus.error = error.message;
  });
setInterval(() => render(performance.now()), 1000 / 15);
