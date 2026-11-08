import * as THREE from "three";
import {
  ACTIVE_PHASES,
  CAMERA_PHASES,
  nextCameraPhase,
} from "./camera-phase.js";

const SUPERSEDED_REQUEST_MESSAGE = "A newer camera request replaced this one";

export function preferredCamera(devices) {
  const physical = devices.filter(
    (device) =>
      device.kind === "videoinput" && !/Avatar Cam/i.test(device.label),
  );
  return (
    physical.find((device) => !/integrated/i.test(device.label)) ?? physical[0]
  );
}

export class CameraLayer {
  constructor(onEnded) {
    this.onEnded = onEnded;
    this.video = document.createElement("video");
    this.video.muted = true;
    this.video.playsInline = true;
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
    this.camera.position.z = 1;
    this.material = new THREE.MeshBasicMaterial();
    this.plane = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.material);
    this.scene.add(this.plane);
    this.phase = { name: CAMERA_PHASES.OFF };
    this.requests = 0;
  }

  get active() {
    return ACTIVE_PHASES.includes(this.phase.name);
  }

  async enablePreferred() {
    const generation = this.openRequest();
    const camera = preferredCamera(
      await navigator.mediaDevices.enumerateDevices(),
    );
    this.requireCurrentRequest(generation);
    if (!camera)
      this.abandonRequest(
        generation,
        new Error("No physical camera is connected"),
      );
    await this.enable(camera.deviceId);
  }

  async enable(deviceId) {
    const generation = this.openRequest();
    const stream = await navigator.mediaDevices
      .getUserMedia({
        video: deviceId ? { deviceId: { exact: deviceId } } : true,
        audio: false,
      })
      .catch((error) => this.abandonRequest(generation, error));
    this.requireCurrentRequest(generation, stream);
    this.requireExternalCamera(stream);
    this.moveTo({ type: "ready", generation, stream });
    stream.getVideoTracks().forEach((track) => {
      track.addEventListener("ended", () => this.endLiveStream(stream), {
        once: true,
      });
    });
    this.video.srcObject = stream;
    await this.video.play();
    this.requireCurrentRequest(generation);
    this.material.map = new THREE.VideoTexture(this.video);
    this.material.map.encoding = THREE.sRGBEncoding;
    this.material.needsUpdate = true;
  }

  openRequest() {
    this.requests += 1;
    this.moveTo({ type: "open", generation: this.requests });
    return this.requests;
  }

  isCurrentRequest(generation) {
    return (
      [CAMERA_PHASES.OPENING, CAMERA_PHASES.LIVE].includes(this.phase.name) &&
      this.phase.generation === generation
    );
  }

  requireCurrentRequest(generation, stream) {
    if (this.isCurrentRequest(generation)) return;
    if (stream) for (const track of stream.getTracks()) track.stop();
    throw new Error(SUPERSEDED_REQUEST_MESSAGE);
  }

  abandonRequest(generation, error) {
    if (this.isCurrentRequest(generation)) this.disable();
    throw error;
  }

  requireExternalCamera(stream) {
    if (
      stream.getVideoTracks().some((track) => /Avatar Cam/i.test(track.label))
    ) {
      for (const track of stream.getTracks()) track.stop();
      this.moveTo({ type: "release" });
      throw new Error("Choose a physical camera rather than Avatar Cam");
    }
  }

  endLiveStream(stream) {
    if (this.phase.name !== CAMERA_PHASES.LIVE || this.phase.stream !== stream)
      return;
    this.disable();
    this.onEnded();
  }

  enableSynthetic() {
    const canvas = document.createElement("canvas");
    canvas.width = 640;
    canvas.height = 360;
    this.moveTo({ type: "synthetic", canvas });
    this.material.map = new THREE.CanvasTexture(canvas);
    this.material.needsUpdate = true;
  }

  render(renderer, timestamp, mouth) {
    const syntheticCanvas =
      this.phase.name === CAMERA_PHASES.SYNTHETIC ? this.phase.canvas : null;
    const aspect = syntheticCanvas
      ? 16 / 9
      : this.video.videoWidth / this.video.videoHeight;
    this.plane.scale.set(
      Math.max(1, aspect / (16 / 9)),
      Math.max(1, 16 / 9 / aspect),
      1,
    );
    if (syntheticCanvas) {
      const context = syntheticCanvas.getContext("2d");
      context.fillStyle = "#2362a8";
      context.fillRect(0, 0, 640, 360);
      context.fillStyle = "white";
      context.font = "36px sans-serif";
      context.fillText("Synthetic camera", 35, 180);
      context.fillRect((timestamp / 10) % 600, 30, 30, 30);
      context.fillStyle = mouth > 0.01 ? "white" : "black";
      context.fillRect(0, 0, 40, 40);
      this.material.map.needsUpdate = true;
    }
    renderer.render(this.scene, this.camera);
  }

  moveTo(event) {
    const nextPhase = nextCameraPhase(this.phase, event);
    if (nextPhase === this.phase) return;
    this.releasePhase(this.phase);
    this.phase = nextPhase;
  }

  releasePhase(phase) {
    if (phase.name === CAMERA_PHASES.LIVE) {
      for (const track of phase.stream.getTracks()) track.stop();
      this.video.srcObject = null;
    }
    this.material.map?.dispose();
    this.material.map = null;
  }

  disable() {
    this.moveTo({ type: "release" });
  }
}
