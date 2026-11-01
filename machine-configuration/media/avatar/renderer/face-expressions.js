const FACE_EXPRESSIONS = {
  happy: { upperFace: { BRW_Joy: 1, EYE_Joy: 1 }, mouth: { MTH_Fun: 1 } },
  excited: {
    upperFace: { BRW_Surprised: 0.8, EYE_Joy: 0.5 },
    mouth: { MTH_Joy: 0.8 },
  },
  relaxed: { upperFace: { BRW_Fun: 1, EYE_Joy: 0.3 }, mouth: { MTH_Fun: 0.7 } },
  sad: { upperFace: { BRW_Sorrow: 1, EYE_Sorrow: 1 }, mouth: { MTH_Sorrow: 1 } },
  worried: {
    upperFace: { BRW_Sorrow: 0.8, EYE_Sorrow: 0.4 },
    mouth: { MTH_Sorrow: 0.5 },
  },
  angry: { upperFace: { BRW_Angry: 1, EYE_Angry: 1 }, mouth: { MTH_Angry: 1 } },
  determined: {
    upperFace: { BRW_Angry: 0.6, EYE_Angry: 0.25 },
    mouth: { MTH_Fun: 0.4 },
  },
  surprised: {
    upperFace: { BRW_Surprised: 1, EYE_Surprised: 1 },
    mouth: { MTH_Surprised: 1 },
  },
  thinking: {
    upperFace: { BRW_Sorrow: 0.45, EYE_Close_R: 0.35 },
    mouth: { MTH_Neutral: 1 },
  },
  shy: { upperFace: { BRW_Sorrow: 0.6, EYE_Joy: 0.4 }, mouth: { MTH_Fun: 0.5 } },
  smug: {
    upperFace: { BRW_Fun: 0.6, EYE_Close_L: 0.35, EYE_Close_R: 0.35 },
    mouth: { MTH_Fun: 0.8 },
  },
  wink: { upperFace: { BRW_Joy: 0.5, EYE_Close_R: 1 }, mouth: { MTH_Fun: 0.9 } },
  sleepy: {
    upperFace: { BRW_Sorrow: 0.3, EYE_Close: 0.65 },
    mouth: { MTH_Neutral: 1 },
  },
};
const PRESET_EXPRESSIONS_REPLACED = [
  "happy",
  "angry",
  "sad",
  "relaxed",
  "surprised",
  "Surprised",
];
const VOWEL_LINGER_SECONDS = 0.12;

class MorphBind {
  constructor(meshes, index, weight) {
    this.meshes = meshes;
    this.index = index;
    this.weight = weight;
  }

  applyWeight(weight) {
    for (const mesh of this.meshes)
      mesh.morphTargetInfluences[this.index] += this.weight * weight;
  }

  clearAppliedWeight() {
    for (const mesh of this.meshes) mesh.morphTargetInfluences[this.index] = 0;
  }
}

function morphIndex(morphNames, suffix) {
  return morphNames.findIndex((name) => name.endsWith(`Fcl_${suffix}`));
}

export function faceMorphNames(gltfDocument) {
  return gltfDocument.meshes
    .map(
      (mesh) =>
        mesh.extras?.targetNames ?? mesh.primitives[0].extras?.targetNames ?? [],
    )
    .find((morphNames) => morphIndex(morphNames, "MTH_A") >= 0);
}

export function expressionMouthName(expression) {
  return `${expression}Mouth`;
}

export function expressionNames() {
  return ["neutral", ...Object.keys(FACE_EXPRESSIONS)];
}

export function registerFaceExpressions(vrm, morphNames, createExpression) {
  const faceMeshes = [];
  vrm.scene.traverse((node) => {
    if (node.morphTargetInfluences?.length === morphNames.length)
      faceMeshes.push(node);
  });
  const manager = vrm.expressionManager;
  const registerMorphExpression = (name, morphWeights) => {
    const expression = createExpression(name);
    for (const [suffix, weight] of Object.entries(morphWeights)) {
      const index = morphIndex(morphNames, suffix);
      if (index >= 0)
        expression.addBind(new MorphBind(faceMeshes, index, weight));
    }
    manager.registerExpression(expression);
  };
  for (const name of PRESET_EXPRESSIONS_REPLACED) {
    const preset = manager.getExpression(name);
    if (preset) manager.unregisterExpression(preset);
  }
  for (const [name, face] of Object.entries(FACE_EXPRESSIONS)) {
    registerMorphExpression(name, face.upperFace);
    registerMorphExpression(expressionMouthName(name), face.mouth);
  }
}

export function vowelShapeAt(vowels, seconds) {
  const vowel = vowels.find(
    ({ start, end }) => seconds >= start && seconds < end + VOWEL_LINGER_SECONDS,
  );
  return vowel?.shape ?? "aa";
}
