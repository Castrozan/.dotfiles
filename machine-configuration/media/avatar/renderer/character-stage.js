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
    this.characters = [];
    this.vrm = null;
    this.name = null;
    this.performer = null;
  }

  async open() {
    const response = await fetch("/characters.json");
    this.characters = await response.json();
    await this.show(this.characters[0].name);
  }

  async show(name) {
    const names = this.characters.map((character) => character.name);
    if (!names.includes(name))
      throw new Error(
        `Unknown character ${name}; choose one of ${names.join(", ")}`,
      );
    const gltf = await this.loader.loadAsync(`/characters/${name}.vrm`);
    const vrm = gltf.userData.vrm;
    VRMUtils.rotateVRM0(vrm);
    vrm.scene.updateMatrixWorld(true);
    const focusHeight = this.focusHeightOf(vrm);
    const performer = new AvatarPerformer({
      vrm,
      morphNames: faceMorphNames(gltf.parser.json),
      gazeTarget: this.gazeTarget,
      gazeOrigin: new THREE.Vector3(0, focusHeight, 1),
      createExpression: (expressionName) => new VRMExpression(expressionName),
      characters: this.characters,
    });
    this.scene.add(vrm.scene);
    this.camera.position.set(0, focusHeight, 1);
    this.camera.lookAt(0, focusHeight, 0);
    if (this.vrm) {
      this.scene.remove(this.vrm.scene);
      VRMUtils.deepDispose(this.vrm.scene);
    }
    this.vrm = vrm;
    this.name = name;
    this.performer = performer;
  }

  focusHeightOf(vrm) {
    const head = vrm.humanoid.getNormalizedBoneNode("head");
    const headPosition = new THREE.Vector3();
    head.getWorldPosition(headPosition);
    return headPosition.y - 0.04;
  }
}
