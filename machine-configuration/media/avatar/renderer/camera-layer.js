import * as THREE from "three";

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
    this.stream = null;
    this.syntheticCanvas = null;
  }

  get active() {
    return Boolean(this.stream || this.syntheticCanvas);
  }

  async enable(deviceId) {
    this.disable();
    const stream = await navigator.mediaDevices.getUserMedia({
      video: deviceId ? { deviceId: { exact: deviceId } } : true,
      audio: false,
    });
    this.requireExternalCamera(stream);
    this.stream = stream;
    stream.getVideoTracks().forEach((track) => {
      track.addEventListener(
        "ended",
        () => {
          this.disable();
          this.onEnded();
        },
        { once: true },
      );
    });
    this.video.srcObject = stream;
    await this.video.play();
    this.material.map = new THREE.VideoTexture(this.video);
    this.material.map.encoding = THREE.sRGBEncoding;
    this.material.needsUpdate = true;
  }

  requireExternalCamera(stream) {
    if (
      stream.getVideoTracks().some((track) => /Avatar Cam/i.test(track.label))
    ) {
      stream.getTracks().forEach((track) => {
        track.stop();
      });
      throw new Error("Choose a physical camera rather than Avatar Cam");
    }
  }

  enableSynthetic() {
    this.disable();
    this.syntheticCanvas = document.createElement("canvas");
    this.syntheticCanvas.width = 640;
    this.syntheticCanvas.height = 360;
    this.material.map = new THREE.CanvasTexture(this.syntheticCanvas);
    this.material.needsUpdate = true;
  }

  render(renderer, timestamp, mouth) {
    const aspect = this.syntheticCanvas
      ? 16 / 9
      : this.video.videoWidth / this.video.videoHeight;
    this.plane.scale.set(
      Math.max(1, aspect / (16 / 9)),
      Math.max(1, 16 / 9 / aspect),
      1,
    );
    if (this.syntheticCanvas) {
      const context = this.syntheticCanvas.getContext("2d");
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

  disable() {
    this.stream?.getTracks().forEach((track) => {
      track.stop();
    });
    this.stream = null;
    this.syntheticCanvas = null;
    this.video.srcObject = null;
    this.material.map?.dispose();
    this.material.map = null;
  }
}
