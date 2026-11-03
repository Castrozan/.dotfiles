import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { VRMExpression, VRMLoaderPlugin, VRMUtils } from "@pixiv/three-vrm";
import { AvatarPerformer } from "./avatar-performer.js";
import { faceMorphNames } from "./face-expressions.js";

export class CharacterStage {
  constructor(scene, camera) {
    this.scene = scene;
    this.camera = camera;
    this.loader = new GLTFLoader();
    this.loader.register((parser) => new VRMLoaderPlugin(parser));
    this.gazeTarget = new THREE.Object3D();
    scene.add(this.gazeTarget);
    this.names = [];
    this.vrm = null;
    this.performer = null;
  }

  async open() {
    const response = await fetch("/characters.json");
    this.names = await response.json();
    await this.show(this.names[0]);
  }

  async show(name) {
    if (!this.names.includes(name))
      throw new Error(
        `Unknown character ${name}; choose one of ${this.names.join(", ")}`,
      );
    const gltf = await this.loader.loadAsync(`/characters/${name}.vrm`);
    const vrm = gltf.userData.vrm;
    VRMUtils.rotateVRM0(vrm);
    this.scene.add(vrm.scene);
    vrm.scene.updateMatrixWorld(true);
    this.frameHead(vrm);
    if (this.vrm) {
      this.scene.remove(this.vrm.scene);
      VRMUtils.deepDispose(this.vrm.scene);
    }
    this.vrm = vrm;
    this.performer = new AvatarPerformer({
      vrm,
      morphNames: faceMorphNames(gltf.parser.json),
      gazeTarget: this.gazeTarget,
      gazeOrigin: this.camera.position.clone(),
      createExpression: (expressionName) => new VRMExpression(expressionName),
      characterNames: this.names,
    });
  }

  frameHead(vrm) {
    const head = vrm.humanoid.getNormalizedBoneNode("head");
    const headPosition = new THREE.Vector3();
    head.getWorldPosition(headPosition);
    this.camera.position.set(0, headPosition.y - 0.04, 1);
    this.camera.lookAt(0, headPosition.y - 0.04, 0);
  }
}
